import datetime
from PyQt5.QtCore import QObject, QModelIndex, Qt, pyqtSlot, pyqtSignal, QTimer, QPersistentModelIndex
from PyQt5.QtWidgets import QActionGroup, QAction, QMenu, QWidgetAction, QCheckBox, QSpinBox, QLineEdit, \
    QAbstractSpinBox

from Models.Tymbox.TymboxModel import TymboxModel, TymboxTask, TymboxModelColumns, TymboxTask
from Utils.LogHelper import LogHelper


class TymboxAssistant(QObject, LogHelper):

    task_ended = pyqtSignal(TymboxTask, name='taskEnded')

    def __init__(self, parent: QObject, model: TymboxModel):
        QObject.__init__(self, parent)
        LogHelper.__init__(self, "TymboxAssistant")
        self.model = model

        self.action_map = dict()

        self.current_task = None
        self.current_task_index = None
        self.task_end_timer = QTimer()
        self.task_end_timer.setSingleShot(True)
        self.task_end_timer.timeout.connect(self.__on_task_ended)

        current_task_actions = QActionGroup(self)

        self.end_current_task_action = QAction("End current task", self)
        self.end_current_task_action.setObjectName("EndCurrentTask")
        self.end_current_task_action.triggered.connect(self.end_current_task)

        self.current_task_name = QAction(self)
        self.current_task_name.setDisabled(True)

        self.remaining_time_action = QAction(self)
        self.remaining_time_action.setEnabled(False)
        self.remaining_time_action.setObjectName("RemainingTime")

        self.remaining_time_update_timer = QTimer()
        self.remaining_time_update_timer.setSingleShot(False)
        self.remaining_time_update_timer.setInterval(1000)
        self.remaining_time_update_timer.start()
        self.remaining_time_update_timer.timeout.connect(self.__on_update_remaining_time)

        current_task_actions.addAction(self.current_task_name)
        sep = QAction(self)
        sep.setSeparator(True)
        current_task_actions.addAction(sep)
        current_task_actions.addAction(self.remaining_time_action)
        current_task_actions.addAction(self.end_current_task_action)
        current_task_actions.setVisible(False)

        self.action_map["Current Task"] = current_task_actions

        self.task_name_edit = QLineEdit()
        self.task_name_edit.setPlaceholderText("Task Name")

        self.task_duration_spin = QSpinBox()
        self.task_duration_spin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.task_duration_spin.setMaximum(600)
        self.task_duration_spin.setValue(30)
        self.task_duration_spin.setMinimum(15)
        self.task_duration_spin.setSuffix(" minutes")
        self.task_duration_spin.setPrefix("Duration: ")

        self.task_come_back_checkbox = QCheckBox()
        self.task_come_back_checkbox.setChecked(True)
        self.task_come_back_checkbox.setText("Come back to current task")

        add_task_group = QActionGroup(self)

        task_name_action = QWidgetAction(self)

        task_name_action.setDefaultWidget(self.task_name_edit)
        add_task_group.addAction(task_name_action)

        task_duration_action = QWidgetAction(self)
        task_duration_action.setDefaultWidget(self.task_duration_spin)
        add_task_group.addAction(task_duration_action)

        task_come_back_action = QWidgetAction(self)
        task_come_back_action.setDefaultWidget(self.task_come_back_checkbox)
        add_task_group.addAction(task_come_back_action)

        start_task_action = QAction("Start Task", self)
        start_task_action.setObjectName("StartTask")
        start_task_action.triggered.connect(self.__on_start_task)
        add_task_group.addAction(start_task_action)

        self.action_map["Add Task"] = add_task_group


        model.dataChanged.connect(self.on_model_data_changed)
        model.rowsInserted.connect(self.on_model_row_inserted, Qt.QueuedConnection)

    def __on_update_remaining_time(self):
        if self.current_task is not None:
            current_time = datetime.datetime.today().timestamp()
            remaining_s = self.current_task.end_time - current_time
            remaining_str = datetime.datetime(year=2017, month=8, day=6, hour=int((remaining_s/(60*60))%24),
                                              minute=int((remaining_s/60)%60),
                                              second=int(remaining_s%60)).strftime('%H:%M:%S')
            self.remaining_time_action.setText("Remaining time: %s" % str(remaining_str))


    def end_current_task(self):
        if self.current_task_index is not None:
            current_time = datetime.datetime.today().timestamp()
            self.model.setData(self.current_task_index.sibling(self.current_task_index.row(), TymboxModelColumns.end_time), current_time)
            self.log_info("Ended current task")

    def __on_start_task(self):
        task_name = self.task_name_edit.text()
        self.task_name_edit.setText("")
        self.task_name_edit.clearFocus()

        task_duration = self.task_duration_spin.value() * 60
        self.task_duration_spin.setValue(30)

        come_back = self.task_come_back_checkbox.isChecked()
        self.task_come_back_checkbox.setChecked(True)

        self.log_debug("on_start_task", name=task_name, duration=task_duration, come_back=come_back)
        self.model.interrupt_current_task(task_name, task_duration, come_back)

    def __on_task_ended(self):
        self.log_debug("Task ended", current_task=self.current_task)
        if self.current_task is not None:
            self.task_ended.emit(self.current_task)
            self.__clear_current_task()

    def __update_current_task(self, index: QModelIndex, task: TymboxTask):
        self.current_task = task
        self.current_task_index = QPersistentModelIndex(index) if task is not None else None
        current_time = datetime.datetime.today().timestamp()
        remaining_s = task.end_time - current_time

        self.log_debug("Current task updated", remaining_seconds=remaining_s)
        self.current_task_name.setText(self.current_task.name)
        self.task_end_timer.start(remaining_s*1000)
        self.__on_update_remaining_time()
        self.action_map["Current Task"].setVisible(True)

    def __clear_current_task(self):
        self.current_task = None
        self.current_task_index = None
        self.task_end_timer.stop()
        self.current_task_name.setText("")
        self.action_map["Current Task"].setVisible(False)
        self.remaining_time_action.setText("")

    def __scan_rows(self, start: int, end: int):

        current_time = datetime.datetime.today().timestamp()
        for row_number in range(start, end+1):
            event = self.model.get_event(row_number)
            if event.start_time <= current_time < event.end_time:
                self.__update_current_task(self.model.index(row_number, 0), event)
            elif event == self.current_task:
                self.__clear_current_task()


    @pyqtSlot(QModelIndex, QModelIndex)
    def on_model_data_changed(self, top_left: QModelIndex, bottom_right: QModelIndex, roles=None):
        if top_left.column() <= TymboxModelColumns.start_time <= bottom_right.column() \
                or top_left.column() <= TymboxModelColumns.end_time <= bottom_right.column():
            self.log_extra_debug("Handling modified rows: ", top=top_left.row(), bottom=bottom_right.row())
            self.__scan_rows(top_left.row(), bottom_right.row())

    @pyqtSlot(QModelIndex, int, int)
    def on_model_row_inserted(self, parent: QModelIndex, first: int, last: int):
        self.log_extra_debug("Handling inserted rows: ", first=first, last=last)
        self.__scan_rows(first, last)