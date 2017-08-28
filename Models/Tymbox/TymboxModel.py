import datetime
import json
from enum import IntEnum, unique

import math
from PyQt5.QtCore import QModelIndex, Qt, QMimeData, QTextStream, QByteArray, QDataStream, QIODevice

from Models.ExtendableItemModel import ExtendableItemModel, ItemModelDataSetType, ItemModelDataSet
from Models.Trello.TrelloCardsModel import TrelloCardsModel


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
            if type_name == cls.type:
                return cls()
        return None

@unique
class TymboxTaskTimePreference(IntEnum):
    preferred       = 0                 # Try to start task at preference
    sequential      = preferred + 1     # No preference, start asap
    start_at        = preferred + 2     # Must start at preference
    end_no_later    = preferred + 3     # Must end before preference
    duration        = preferred + 4     # Minimum duration, start asap
    fixed           = preferred + 5     # Cannot implicitly move


class TymboxEvent(object):
    type = "Event"

    def __init__(self):
        self.end_time = 60
        self.name = ""
        self.start_time = 0
        self.preference_value = 0
        self.time_preference = TymboxTaskTimePreference.preferred

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

    @classmethod
    def deserialise(cls, data):
        instance = cls()
        instance.name = data["name"]
        instance.end_time = data["duration"]
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
    name                = 0
    type                = name + 1
    start_time          = name + 2
    end_time            = name + 3
    preference_value    = name + 4
    time_preference     = name + 5

TymboxModelColumnsCount = len(list(TymboxModelColumns))

class TymboxModel(ExtendableItemModel):
    def __init__(self, parent=None):
        ExtendableItemModel.__init__(self, parent)
        self.duration = 8*60*60
        self.start_time = datetime.datetime.today().replace(hour=12, minute=0, second=0, microsecond=0).timestamp()
        self.tasks = []
        self.cards_model = None
        self.next_task_to_insert = None

    def _register_columns(self):
        data_set = self.add_data_set("TymboxModelDS", self.tasks, ItemModelDataSetType.Obj, True)
        self.add_columns(TymboxModelColumns, data_set)

        self.set_column_formatter(TymboxModelColumns.start_time, self._time_formatter )
        self.set_column_formatter(TymboxModelColumns.end_time, self._time_formatter )
        self.set_column_formatter(TymboxModelColumns.preference_value, self._time_formatter )

    @staticmethod
    def _time_formatter(i: float):
        return datetime.datetime.fromtimestamp(i).strftime('%H:%M:%S')

    @staticmethod
    def _duration_formatter(i: int):
        return datetime.time(hour=int(math.floor(i/60)), minute=i%60).strftime('%H:%M:%S')

    def set_start_time(self, start_time: int):
        self.start_time = start_time
        # TODO clear
        # TODO remove_rows

    def set_duration(self, duration: int):
        self.duration = duration

    def set_cards_model(self, model: TrelloCardsModel):
        self.cards_model = model

    def get_event(self, row: int) -> TymboxEvent:
        return self.tasks[row]

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def supportedDragActions(self):
        return Qt.MoveAction

    def flags(self, index: QModelIndex):
        default_flags = ExtendableItemModel.flags(self, index)

        default_flags |= Qt.ItemIsDropEnabled

        if index.isValid():
            default_flags |= Qt.ItemIsDragEnabled

        return default_flags

    def __insert_task(self, at, task: TymboxEvent):
        self.next_task_to_insert = task
        self.insertRow(at)
        self.next_task_to_insert = None

    def append_task(self, name, duration, time_preference = TymboxTaskTimePreference.preferred, preference_value = None):
        task = TymboxTask()
        task.name = name
        task.start_time = self.tasks[-1].end_time if len(self.tasks) else self.start_time
        task.end_time = task.start_time + duration
        task.time_preference = time_preference
        task.preference_value = task.start_time if preference_value is None else preference_value
        self.__insert_task(len(self.tasks), task)

    def remove_task(self, at):
        self.removeRow(at)

    def construct_data_source(self, data_set: ItemModelDataSet, pos: int):
        if data_set.id == "TymboxModelDS":
            if self.next_task_to_insert is None:
                print("construct called for task")
                return TymboxEvent()
            else:
                print("construct called for inserted task")
                return self.next_task_to_insert
        return ExtendableItemModel.construct_data_source(self, data_set, pos)

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

            self.tasks[from_row] = TymboxEvent()
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

            task.start_time = self.tasks[-1].end_time if len(self.tasks) else self.start_time
            task.preference_value = task.start_time

            self.__insert_task(len(self.tasks), task)
        else:
            task.start_time = self.tasks[row].start_time
            task.preference_value = self.tasks[row].start_time
            self.tasks[row] = task
            self.dataChanged.emit(self.index(row, 0), self.index(row, TymboxModelColumnsCount))

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
