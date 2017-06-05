import datetime
import pprint
from enum import IntEnum
import time
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QMimeData, QTextStream, QByteArray, QDataStream, QVariant, QIODevice
import json

from TrelloCardsModel import TrelloCardsModel


class TymboxTaskFactory(object):
    classes = list()

    @staticmethod
    def register(cls):
        TymboxTaskFactory.classes.append(cls)
        print("TymboxTaskFactory: Registered task with type '%s'" % cls.type)
        return cls

    @staticmethod
    def deserialise(data):
        if "type" in data:
            type_name = data["type"]
            for cls in TymboxTaskFactory.classes:
                if cls.type == type_name:
                    return cls.deserialise(data)
        return None

    @staticmethod
    def create(type_name: str):
        for cls in TymboxTaskFactory.classes:
            if type == serialise_type:
                return cls()
        return None

class TymboxTaskStartType(IntEnum):
    preferred = 0
    sequential = 1
    fixed = 2
    no_later = 3
    no_earlier = 4

class TymboxEvent(TymboxSerialisable):
    type = "Event"

    def __init__(self):
        self.duration = 60
        self.name = ""
        self.start_time = 0
        self.preferred_start_time = 0
        self.preferred_duration = 0
        self.start_type = TymboxTaskStartType.preferred
        self.drag

    def get_end_time(self) -> int:
        return self.start_time + self.duration

    @classmethod
    def deserialise(cls, data):
        instance = cls()
        instance.name = data["name"]
        instance.duration = data["duration"]
        return instance

    def serialise(self) -> dict():
        data = dict()
        data["type"] = self.type
        data["name"] = self.name
        data["duration"] = self.duration
        return data


@TymboxTaskFactory.register
class TymboxTask(TymboxEvent):
    type = "Task"


@TymboxTaskFactory.register
class TymboxTrelloTask(TymboxTask):
    type = "TrelloTask"

    def __init__(self):
        super().__init__()
        self.card_id = ""

    @classmethod
    def deserialise(cls, data):
        instance = super().deserialise(data)
        instance.card_id = data["trello_card_id"]
        return instance

    def serialise(self) -> dict():
        data = super().serialise()
        data["trello_card_id"] = self.card_id
        return data


class TymboxModelColumns(IntEnum):
    name = 0
    type = 1
    start_time = 2
    duration = 3


class TymboxModel(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.blocks = 9
        self.duration = 540
        self.start_time = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        self.tasks = [] # [TymboxGap(int(self.duration/self.blocks), int(self.start_time+i*self.duration/self.blocks)) for i in range(0, self.blocks)]
        self.cards_model = None



    def set_cards_model(self, model: TrelloCardsModel):
        self.cards_model = model

    def get_event(self, row: int):
        return self.tasks[row]

    def get_overlapping_event(self, row):
        if row+1 < len(self.tasks):
            event = self.get_event(row)
            next_event = self.get_event(row+1)
            if event.get_end_time() > next_event.start_time:
                return next_event
        return None

    def alter_event_start_time(self, row, amount_s):
        index = self.index(row, TymboxModelColumns.start_time)
        event = self.get_event(row)
        self.setData(index, event.start_time + amount_s)
        overlapping_event = self.get_overlapping_event(row)
        if overlapping_event is not None:
            print("alter start: ", event.name, "is overlapping", overlapping_event.name, "by", event.get_end_time() - overlapping_event.start_time)
            self.alter_event_start_time(row+1, event.get_end_time() - overlapping_event.start_time)
        elif row+1 < len(self.tasks):
            self.bring_to_preferred_start(row+1)

    def alter_event_duration(self, row, amount_s):
        event = self.get_event(row)
        self.setData(self.index(row, TymboxModelColumns.duration), event.duration + amount_s)
        overlapping_event = self.get_overlapping_event(row)
        if overlapping_event is not None:
            print("alter duration: ", event.name, "is overlapping", overlapping_event.name, "by",
                  event.get_end_time() - overlapping_event.start_time)
            self.alter_event_start_time(row+1, event.get_end_time() - overlapping_event.start_time)
        elif row+1 < len(self.tasks):
            self.bring_to_preferred_start(row+1)

    def bring_to_preferred_start(self, row):
        event = self.get_event(row)
        if event.preferred_start_time < event.start_time:
            if row != 0:
                previous_event = self.get_event(row-1)
                print("bring to preferred start time:", event.name, event.preferred_start_time, event.start_time)
                if event.preferred_start_time >= previous_event.get_end_time():
                    self.alter_event_start_time(row, event.preferred_start_time - event.start_time)
                else:
                    self.alter_event_start_time(row, previous_event.get_end_time() - event.start_time)


    def data(self, index: QModelIndex, role=None):
        if not index.isValid() or index.row() > self.rowCount() or index.column() > self.columnCount():
            return None
        if role == Qt.DisplayRole:
            space = self.get_event(index.row())
            column_name = str(TymboxModelColumns(index.column()).name)
            return getattr(space, column_name, None)
        return None

    def setData(self, index: QModelIndex, data, role=Qt.EditRole):
        if not index.isValid() or index.row() > self.rowCount() or index.column() > self.columnCount():
            print("index invalid or out of range")
            return False
        if role == Qt.EditRole:
            space = self.get_event(index.row())
            column_name = str(TymboxModelColumns(index.column()).name)
            setattr(space, column_name, data)
            self.dataChanged.emit(index, index)
            # print("set data")
            return True
        print("unhandled role")
        return False

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.tasks)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(list(TymboxModelColumns))

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def supportedDragActions(self):
        return Qt.MoveAction

    def flags(self, index: QModelIndex):
        default_flags = QAbstractTableModel.flags(self, index)

        default_flags |= Qt.ItemIsDropEnabled

        if index.isValid():
            if not self.get_event(index.row()).type == "Gap":
                default_flags |= Qt.ItemIsDragEnabled

        return default_flags

    def insertRows(self, row, count, parent=None, *args, **kwargs):
        self.beginInsertRows(parent, row, row + count)
        for i in range(row, row+count):
            self.tasks.insert(i, TymboxGap())
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None, *args, **kwargs):
        self.beginRemoveRows(parent, row, row+count)
        for i in range(1, count):
            self.tasks.remove(row)
        self.endInsertRows()
        return True

    def mimeTypes(self):
        return ["application/json", "application/x-dnd-indices"]


    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex):
        return super().canDropMimeData(data, action, row, column, parent)

    def dropMimeData(self, mime_data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex):

        if action == Qt.IgnoreAction:
            print("ignore action")
            return True

        if action == Qt.MoveAction:
            data = mime_data.data("application/x-dnd-indices")
            if data is None:
                print("No data in move")
                return False

            index_list = QDataStream(data, QIODevice.ReadOnly).readQVariantList()
            if index_list is None:
                print("No index list")
                return False

            if len(index_list) == 0:
                print("Empty index list")
                return False

            for i in index_list:
                print("inbound", i)

            from_row = index_list[0]
            task = self.get_event(from_row)
            print("Moving task %s" % task.name)

            self.tasks[from_row] = TymboxGap()
            self.dataChanged.emit(self.index(from_row, 0), self.index(from_row, 1))

        elif action == Qt.CopyAction:
            if not mime_data.hasFormat("application/json"):
                return False

            byte_array = mime_data.data("application/json")
            json_str = QTextStream(byte_array).readAll()

            print("Importing MIME: %s" % json_str)
            json_data = json.loads(json_str)
            if not json_data:
                print("Null json data")
                return False

            if "dataType" not in json_data:
                print("No dataType")
                return False

            data_type = json_data["dataType"]

            task = None
            if data_type == "TrelloCardIds":
                if "TrelloCardIds" not in json_data:
                    print("No TrelloCardIds")
                    return False

                card_id_list = json_data["TrelloCardIds"]
                if len(card_id_list) == 0:
                    print("Empty card id list")
                    return False

                card_id = card_id_list[0]
                card = self.cards_model.get_card_by_id(card_id)
                if not card:
                    print("Unable to get card from Id")
                    return False

                task = TymboxTrelloTask()
                task.name = card.name
                task.card_id = card_id

            elif data_type == "TymboxTasks":
                if "TymboxTasks" not in json_data:
                    print("No TymboxTasks")
                    return False

                task_list = json_data["TymboxTasks"]
                if len(task_list) == 0:
                    print("Empty task list")
                    return False

                task_json = task_list[0]

                task = TymboxTaskFactory.deserialise(task_json)
                if task is None:
                    print("Cannot create task from json")
                    return False

            else:
                print("Unknown dataType '%s'" % data_type)
                return False
        else:
            print("Unhandled action")
            return False

        print(row, column, parent.row(), parent.column())
        if parent.isValid():
            row = parent.row()

        if row == -1 and column == -1:
            # Append
            row = len(self.tasks)
            self.beginInsertRows(QModelIndex(), 0, 0)
            task.start_time = self.tasks[-1].get_end_time() if len(self.tasks) else self.start_time
            task.preferred_start_time = task.start_time
            self.tasks.append(task)
            self.endInsertRows()
        else:
            task.start_time = self.tasks[row].start_time
            task.preferred_start_time = self.tasks[row].start_time
            self.tasks[row] = task
            self.dataChanged.emit(self.index(row, 0), self.index(row, 0))

        return True

    def mimeData(self, index_list: list):
        mime_data = QMimeData()

        """json_data = dict()
        json_data["dataType"] = "TymboxTasks"
        json_data["TymboxTasks"] = list()
        for index in index_list:
            if index.isValid():
                task = self.get_event(index.row())
                json_data["TymboxTasks"].append(task.serialise())

        json_str = json.dumps(json_data)
        print("Exporting MIME: %s" % json_str)
        """
        byte_array = QByteArray()
        QDataStream(byte_array, QIODevice.WriteOnly).writeQVariantList([index.row() for index in index_list])

        mime_data.setData("application/x-dnd-indices", byte_array)
        print(str(byte_array))

        print("Exported mime data with %i indices" % len(index_list))
        print("outbound", index_list[0].row())


        return mime_data
