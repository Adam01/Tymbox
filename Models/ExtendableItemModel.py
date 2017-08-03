from typing import Optional, Callable, Any

import datetime
from PyQt5.QtCore import Qt
from enum import IntEnum
from PyQt5.QtCore import QAbstractItemModel, QModelIndex
from Utils.LogHelper import LogHelper


class ItemModelDataSetType(IntEnum):
    """"
        Types of data sets supported by the extendable item model
    """
    Obj = 0 # Object based data set, columns reference members/properties of objects
    List = 1 # List/array base set, columns reference indices
    ObjTree = 2 # *not yet supported / fully tested* Object tree (for tree models), columns reference members/properties
    Dict = 3 # Dict based set, columns reference keys

class ItemModelColumn:
    """
        Provides information about where column data is from
        Allows for columns to source data from multiple data sets when inheriting
    """
    def __init__(self):
        self.display_name = None
        self.data_id = None
        self.data_set = None
        self.column_no = None
        self.formatter = None

    def get_data_source(self, row_no: int):
        if row_no >= len(self.data_set.src):
            raise IndexError("Row out of range")
        return self.data_set.src[row_no]

    def __repr__(self):
        return "ItemModelColumn(%i:%s %s:%s %s)" % (self.column_no, self.display_name, self.data_set, self.data_id, "Formatted" if self.formatter is not None else "")

class ItemModelDataSet:
    """
        Provides information about a data set
        Adds support for tree structured data sets where parent indices are used
    """
    def __init__(self):
        self.child_nodes_name = None
        self.src = None
        self.type = None
        self.managed = False
        self.id = None

    def __repr__(self):
        return "ItemModelDataSet(%s %s %s Data: %s)"  % (self.id, self.type, "Managed" if self.managed else "", hex(id(self.src)))

class ExtendableItemModel(QAbstractItemModel, LogHelper):
    """
        Item model that supports adding dynamic columns functionally, manages derived data by construct/adding to managed
        sets when rows are added and removing items from those sets when rows are removed.

    """
    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.column_definitions = dict()
        self.data_sets = list()
        self.log_extra_debug("Initialised")

    def add_data_set(self, str_id: str, data_set: list, ds_type: ItemModelDataSetType=ItemModelDataSetType.Obj, managed: bool=False):
        """
            Register a data set with the model (for use with added columns)

        :param str_id: UID of the data set
        :param data_set: Reference to set
        :param ds_type: Type of data set, see ItemModelDataSetType
        :param managed: Whether to manage the data set when rows are removed/added, and when cells are modified
        :return: Internal data set information
        """

        ds = ItemModelDataSet()
        ds.id = str_id
        ds.src = data_set
        ds.type = ds_type
        ds.managed = managed
        self.data_sets.append(ds)
        self.log_extra_debug("Added DS:", repr(self.data_sets[-1]))
        return ds

    def add_column(self, column_no: int, column_name: str, data_set: ItemModelDataSet, data_id, formatter: Optional[Callable[[Any], str]] = None):
        """
            Registers a column associated with a data set
        :param column_no: Model column number
        :param column_name: Name of the column (displayed in horizontal header)
        :param data_set: Reference to internal data set
        :param data_id: Name of member/property(str) if Obj/ObjTree/Dict DS, index if List DS
        :param formatter: Optional data formatter when DisplayRole is requested
        :return: Internal column information
        """
        if column_no in self.column_definitions:
            raise KeyError("Column already exists")
        col = ItemModelColumn()
        col.column_no = column_no
        col.data_id = data_id
        col.data_set = data_set
        col.display_name = column_name
        col.formatter = formatter
        self.column_definitions[column_no] = col
        self.log_extra_debug("Added column:", repr(col))
        return col

    def add_columns(self, enum_class, data_set: ItemModelDataSet):
        """
            Bulk add columns from an enum
            Enum names are used as both display name and data set reference
            Values of the enum items are the column number
        :param enum_class: Class of enum
        :param data_set: Target data set
        """
        assert(data_set.type in [ItemModelDataSetType.Obj, ItemModelDataSetType.Dict])
        for col in enum_class:
            self.add_column(col.value, col.name, data_set, col.name)

    def set_column_formatter(self, column_no: int, formatter: callable):
        if column_no in self.column_definitions:
            col = self.column_definitions[column_no]
            col.formatter = formatter
            self.log_extra_debug("Added formatter:", repr(col))
        else:
            raise KeyError("Column not found")

    def index(self, row: int, column: int, parent=None, *args, **kwargs):
        if 0 <= row < self.rowCount(parent) and 0 <= column < self.columnCount(parent):
            return self.createIndex(row, column, None)

    @staticmethod
    def validate_index(index: QModelIndex) -> None:
        if not index.isValid():
            raise KeyError("Invalid index")

    def get_column_definition(self, column_no: int) -> ItemModelColumn:
        if column_no not in self.column_definitions:
            raise KeyError("Unregistered column")
        return self.column_definitions[column_no]

    def get_data_set_column_value(self, index: QModelIndex, format: bool=False):
        self.validate_index(index)
        col_def = self.get_column_definition(index.column())
        data_source = col_def.get_data_source(index.row())

        data = None

        if col_def.data_set.type in [ItemModelDataSetType.Obj, ItemModelDataSetType.ObjTree]:
            if not hasattr(data_source, col_def.data_id):
                raise KeyError("Data ID not in data source object")
            data = getattr(data_source, col_def.data_id)
        elif col_def.data_set.type == ItemModelDataSetType.Dict:
            if col_def.data_id not in data_source:
                raise KeyError("Data ID not in data source object")
            data = data_source[col_def.data_id]
        elif col_def.data_set.type == ItemModelDataSetType.List:
            if col_def.data_id >= len(data_source):
                raise KeyError("Data ID of data set range")
            data = data_source[col_def.data_id]
        else:
            raise Exception("Unhandled data source type")

        """ self.log_extra_debug("Got managed data",
                             index=index,
                             data_id=col_def.data_id,
                             column_no=col_def.column_no,
                             column=col_def.display_name,
                             value=data)"""

        if format and col_def.formatter is not None:
            return col_def.formatter(data)

        return data

    def set_data_set_column_value(self, index: QModelIndex, value):
        self.validate_index(index)
        col_def = self.get_column_definition(index.column())
        data_source = col_def.get_data_source(index.row())

        if col_def.data_set.type in [ItemModelDataSetType.Obj, ItemModelDataSetType.ObjTree]:
            if not hasattr(data_source, col_def.data_id):
                raise KeyError("Data ID not in data source object")
            setattr(data_source, col_def.data_id, value)
        elif col_def.data_set.type == ItemModelDataSetType.Dict:
            if col_def.data_id not in data_source:
                raise KeyError("Data ID not in data source object")
            data_source[col_def.data_id] = value
        elif col_def.data_set.type == ItemModelDataSetType.List:
            if col_def.data_id >= len(data_source):
                raise KeyError("Data ID of data set range")
            data_source[col_def.data_id] = value
        else:
            raise Exception("Unhandled data source type")

        self.log_extra_debug("Set managed data", index=index,
                                                 data_id=col_def.data_id,
                                                 column_no=col_def.column_no,
                                                 column=col_def.display_name,
                                                 value=value)

        self.dataChanged.emit(index, index)

    def data(self, index: QModelIndex, role=None):
        if role in [Qt.DisplayRole, Qt.EditRole]:
            return self.get_data_set_column_value(index, role == Qt.DisplayRole)
        return None

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            raise Exception("Unhandled setData role")
        self.set_data_set_column_value(index, value)
        return True

    def headerData(self, pos: int, orientation: int, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.get_column_definition(pos).display_name
            else:
                return pos
        return QAbstractItemModel.headerData(self, pos, orientation, role)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.column_definitions)

    def rowCount(self, parent=None, *args, **kwargs):
        if len(self.data_sets):
            return len(self.data_sets[0].src)
        if len(self.column_definitions):
            return len(self.column_definitions[0].data_set)
        return 0

    def construct_data_source(self, data_set: ItemModelDataSet, pos: int):
        if data_set.type == ItemModelDataSetType.List:
            return [None]*self.columnCount()
        elif data_set.type in [ItemModelDataSetType.Obj, ItemModelDataSetType.ObjTree]:
            return None

    def insert_managed_rows(self, pos, count):
        rows_inserted = False
        for data_set in self.data_sets:
            if data_set.managed:
                for i in range(pos, pos+count):
                    row_data = self.construct_data_source(data_set, i)
                    data_set.src.insert(i, row_data)
                    rows_inserted = True

        if rows_inserted:
            for i in range(pos, pos+count):
                row_data = dict()
                for col in self.column_definitions.values():
                    row_data[col.display_name] = str(self.get_data_set_column_value(self.index(pos, col.column_no)))


                self.log_extra_debug("Inserted managed row data",
                                     **row_data)

    def insertRows(self, pos, count, parent=None, *args, **kwargs):
        self.beginInsertRows(parent, pos, pos+count-1)
        self.insert_managed_rows(pos, count)
        self.endInsertRows()
        return True

    def remove_managed_rows(self, pos, count):
        for data_set in self.data_sets:
            if data_set.managed:
                for i in range(pos, pos+count):
                    del data_set.src[pos]

    def removeRows(self, pos, count, parent=None, *args, **kwargs):
        self.beginRemoveRows(parent, pos, pos+count-1)
        self.remove_managed_rows(pos, count)
        self.endRemoveRows()
        return True