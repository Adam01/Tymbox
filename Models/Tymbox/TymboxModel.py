import datetime
import json
from enum import IntEnum, unique

import math
from PyQt5.QtCore import QModelIndex, Qt, QMimeData, QTextStream, QByteArray, QDataStream, QIODevice, pyqtSignal, \
    QObject
from copy import copy


from Models.ExtendableItemModel import ExtendableItemModel, ItemModelDataSetType, ItemModelDataSet
from Models.Trello.TrelloCardsModel import TrelloCardsModel


def time_formatter(i: float):
    return datetime.datetime.fromtimestamp(i).strftime('%H:%M:%S')

def duration_formatter(i: int):
    return datetime.time(hour=int(math.floor(i / 60)), minute=i % 60).strftime('%H:%M:%S')

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

@TymboxTaskFactory.register
class TymboxTask(object):
    type = "Task"

    def __init__(self):
        self.model = None #type: TymboxModel
        self.end_time = 60
        self.name = ""
        self.start_time = 0
        self.preference_value = 0
        self.time_preference = TymboxTaskTimePreference.preferred

    def set_data(self, col: int, value):
        self.model.setData(self.column_index(col), value, Qt.EditRole)

    # Model setters
    def set_end_time(self, value: int):
        self.set_data(TymboxModelColumns.end_time, value)

    def set_start_time(self, value: int):
        self.set_data(TymboxModelColumns.start_time, value)

    def set_name(self, value: str):
        self.set_data(TymboxModelColumns.name, value)

    def set_time_preference(self, value: int):
        self.set_data(TymboxModelColumns.time_preference, value)

    def set_preference_value(self, value: int):
        self.set_data(TymboxModelColumns.preference_value, value)

    # Calculated properties
    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

    @property
    def model_row(self):
        return self.model.row_from_task(self)

    def column_index(self, col: int = 0) -> QModelIndex:
        return self.model.index_from_task(self, col)

    def remove(self):
        self.model.remove_task(self.model_row)

    def __repr__(self):
        return "%s(%s->%s)" % (self.name, time_formatter(self.start_time), time_formatter(self.end_time))

    # Serialisation
    @classmethod
    def deserialise(cls, data):
        instance = cls()
        instance.name = data["name"]
        instance.end_time = data["end_time"]
        instance.start_time = data["start_time"]
        instance.time_preference = TymboxTaskTimePreference[data["time_preference"]]
        instance.preference_value = data["preference_value"]
        return instance

    def serialise(self) -> dict():
        data = dict()
        data["type"] = self.type
        data["name"] = self.name
        data["start_time"] = self.start_time
        data["end_time"] = self.end_time
        data["time_preference"] = self.time_preference.name
        data["preference_value"] = self.preference_value
        return data


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

    durationChanged = pyqtSignal(int)

    def __init__(self, parent=None, name: str ="TymboxModel"):
        ExtendableItemModel.__init__(self, parent, name)
        self.duration = 16*60*60
        self.start_time = datetime.datetime.today().replace(hour=8, minute=0, second=0, microsecond=0).timestamp()
        self.tasks = []
        self.cards_model = None
        self.next_task_to_insert = None

        data_set = self.add_data_set("TymboxModelDS", self.tasks, ItemModelDataSetType.Obj, True)
        self.add_columns(TymboxModelColumns, data_set)

        self.set_column_formatter(TymboxModelColumns.start_time, time_formatter)
        self.set_column_formatter(TymboxModelColumns.end_time, time_formatter)
        self.set_column_formatter(TymboxModelColumns.preference_value, time_formatter)

    def set_start_time(self, start_time: int):
        self.start_time = start_time
        # TODO clear
        # TODO remove_rows

    def set_duration(self, duration: int):
        self.duration = duration
        self.durationChanged.emit(duration)

    def set_cards_model(self, model: TrelloCardsModel):
        self.cards_model = model

    def get_event(self, row: int) -> TymboxTask:
        return self.tasks[row]

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def supportedDragActions(self):
        return Qt.MoveAction

    def row_from_task(self, task: TymboxTask):
        for i, t in enumerate(self.tasks):
            if t == task:
                return i
        return None

    def index_from_task(self, task: TymboxTask, col: int = 0) -> QModelIndex:
        row = self.row_from_task(task)
        if row is not None:
            return self.createIndex(row, col)
        return QModelIndex()

    def flags(self, index: QModelIndex):
        default_flags = ExtendableItemModel.flags(self, index)

        default_flags |= Qt.ItemIsDropEnabled

        if index.isValid():
            default_flags |= Qt.ItemIsDragEnabled

        return default_flags

    def __insert_task(self, task: TymboxTask):
        self.next_task_to_insert = task
        self.insertRow(self.get_insert_row_from_time(task.start_time))
        self.next_task_to_insert = None

    def get_current_task(self) -> (int, TymboxTask):
        current_time = datetime.datetime.today().timestamp()
        for i, task in enumerate(self.tasks):
            if task.start_time <= current_time < task.end_time:
                return i, task
        return -1, None

    def get_tasks_within(self, start_time: int, end_time: int) -> list:
        tasks = list()
        for i, task in enumerate(self.tasks):
            if task.start_time >= start_time < task.end_time or task.start_time >= end_time < task.end_time:
                tasks.append(task)
        return tasks

    def get_insert_row_from_time(self, start_time: int) -> int:
        for i, task in enumerate(self.tasks):
            if task.start_time >= start_time:
                return i
        return len(self.tasks)

    def __create_task(self, name, start_time, end_time, time_preference, preference_value) -> TymboxTask:
        task = TymboxTask()
        task.name = name
        task.start_time = start_time
        task.end_time = end_time
        task.time_preference = time_preference
        task.preference_value = task.start_time if preference_value is None else preference_value
        return task

    def insert_task(self, name: str, start_time: int, duration: int, time_preference = TymboxTaskTimePreference.preferred, preference_value = None):
        if len(self.get_tasks_within(start_time, start_time+duration)):
            return
        self.__insert_task(self.__create_task(name, start_time, start_time+duration, time_preference, preference_value))

    def append_task(self, name, duration, time_preference = TymboxTaskTimePreference.preferred, preference_value = None):
        start_time = self.tasks[-1].end_time if len(self.tasks) else self.start_time
        self.__insert_task(self.__create_task(name, start_time, start_time+duration, time_preference, preference_value))

    def insert_task_after_current(self, name, duration, time_preference = TymboxTaskTimePreference.preferred, preference_value = None):
        current_row, current_task = self.get_current_task()
        start_time = current_task.end_time if current_task is not None else self.start_time
        self.__insert_task(self.__create_task(name, start_time, start_time + duration, time_preference,preference_value))

    def interrupt_current_task(self, name, duration, come_back: bool, time_preference=TymboxTaskTimePreference.preferred, preference_value=None):
        current_time = datetime.datetime.today().timestamp()

        task = self.__create_task(name, current_time, current_time + duration, time_preference, preference_value)

        current_row, current_task = self.get_current_task()

        if current_task is not None:
            resumed_task = copy(current_task) if come_back else None #type: TymboxTask

            current_task.set_end_time(current_time)

            self.__insert_task(task)

            self.log_extra_debug("Interrupt task", come_back=come_back, resumed=resumed_task, task=task, current_task=current_task)

            if resumed_task is not None:
                resumed_task.start_time = task.end_time
                resumed_task.end_time += task.duration
                self.__insert_task(resumed_task)
        else:
            self.__insert_task(task)

    def export_tasks(self) -> list:
        serialised_tasks = list()
        start_of_day = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        for task in self.tasks:
            exported_task = copy(task) # type: TymboxTask
            exported_task.start_time -= start_of_day
            exported_task.end_time -= start_of_day
            exported_task.preference_value -= start_of_day
            serialised_tasks.append(exported_task.serialise())
        return serialised_tasks

    def import_tasks(self, tasks: list, replace=False):
        if replace and self.rowCount() > 0:
            self.removeRows(0, self.rowCount())

        start_of_day = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

        for task in tasks:
            imported_task = TymboxTaskFactory.deserialise(task)
            if imported_task:
                imported_task.start_time += start_of_day
                imported_task.end_time += start_of_day
                imported_task.preference_value += start_of_day
                self.__insert_task(imported_task)
            else:
                self.log_error("Failed to import task", task)

    def remove_task(self, at):
        self.removeRow(at)

    def construct_data_source(self, data_set: ItemModelDataSet, pos: int) -> object:
        if data_set.id == "TymboxModelDS":
            if self.next_task_to_insert is None:
                print("construct called for task")
                task = TymboxTask()
            else:
                print("construct called for inserted task")
                task = self.next_task_to_insert
            task.model = self
            return task
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

            self.tasks[from_row] = TymboxTask()
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

            start_time = self.tasks[-1].end_time if len(self.tasks) else self.start_time
            start_time_data = mime_data.data("application/tymbox-start-time")
            if start_time_data is not None:
                start_time = QDataStream(start_time_data, QIODevice.ReadOnly).readInt()
                self.log_debug("Using start time from mime", start_time=start_time)
            else:
                self.log_warning("No start time in mime")


            task.start_time = start_time
            task.end_time = task.start_time + 60 * 60
            task.preference_value = task.start_time

            self.__insert_task(task)
        else:
            task.start_time = self.tasks[row].start_time
            task.end_time = task.start_time + 60 * 60
            task.preference_value = self.tasks[row].start_time
            self.tasks[row] = task
            self.dataChanged.emit(self.index(row, 0), self.index(row, TymboxModelColumnsCount))

        return True

    def mimeData(self, index_list: list):
        mime_data = QMimeData()


        json_data = dict()
        json_data["dataType"] = "TymboxTasks"
        json_data["TymboxTasks"] = list()
        for index in index_list:
            if index.isValid():
                task = self.get_event(index.row())
                json_data["TymboxTasks"].append(task.serialise())

        json_str = json.dumps(json_data)
        task_byte_array = QByteArray()
        QDataStream(task_byte_array, QIODevice.WriteOnly).writeString(json_str)
        mime_data.setData("application/tymbox-tasks-json", task_byte_array)
        print("Exporting tasks MIME: %s" % json_str)

        index_byte_array = QByteArray()
        QDataStream(index_byte_array, QIODevice.WriteOnly).writeQVariantList([index.row() for index in index_list])

        mime_data.setData("application/x-dnd-indices", index_byte_array)

        print("Exported mime data with %i indices" % len(index_list))


        return mime_data
