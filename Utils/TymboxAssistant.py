import datetime
from PyQt5.QtCore import QObject, QModelIndex, Qt, pyqtSlot, pyqtSignal, QTimer

from Models.Tymbox.TymboxModel import TymboxModel, TymboxTask, TymboxModelColumns
from Utils.LogHelper import LogHelper


class TymboxAssistant(QObject, LogHelper):

    task_ended = pyqtSignal(TymboxTask, name='taskEnded')

    def __init__(self, parent: QObject, model: TymboxModel):
        QObject.__init__(self, parent)
        LogHelper.__init__(self)
        self.model = model
        self.current_task = None
        self.task_end_timer = QTimer()
        self.task_end_timer.setSingleShot(True)
        self.task_end_timer.timeout.connect(self.__on_task_ended)

        model.dataChanged.connect(self.on_model_data_changed)
        model.rowsInserted.connect(self.on_model_row_inserted, Qt.QueuedConnection)

    def __on_task_ended(self):
        self.task_ended.emit(TymboxTask())

    def __update_current_task(self, task: TymboxTask):
        self.current_task = task

        current_time = datetime.datetime.today().timestamp()
        remaining_s = task.end_time - current_time

        self.log_debug("Current task updated", remaining_seconds=remaining_s)

        self.task_end_timer.start(remaining_s*1000)

    def __scan_rows(self, start: int, end: int):
        current_time = datetime.datetime.today().timestamp()
        for row_number in range(start, end+1):
            event = self.model.get_event(row_number)
            if event.start_time <= current_time <= event.end_time:
                self.__update_current_task(event)
                break

    @pyqtSlot(QModelIndex, QModelIndex)
    def on_model_data_changed(self, top_left: QModelIndex, bottom_right: QModelIndex, roles=None):
        if top_left.column() <= TymboxModelColumns.start_time <= bottom_right.column() \
                or top_left.column() <= TymboxModelColumns.duration <= bottom_right.column():
            self.log_extra_debug("Handling modified rows: ", top=top_left.row(), bottom=bottom_right.row())
            self.__scan_rows(top_left.row(), bottom_right.row())

    @pyqtSlot(QModelIndex, int, int)
    def on_model_row_inserted(self, parent: QModelIndex, first: int, last: int):
        self.log_extra_debug("Handling inserted rows: ", first=first, last=last)
        self.__scan_rows(first, last)