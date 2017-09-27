from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget

from Utils.LogHelper import LogHelper
from Utils.TymboxAssistant import TymboxAssistant
from Views.Generated.TymboxAssistantView import Ui_TymboxAssistantView


class TymboxAssistantView(QWidget, LogHelper):
    def __init__(self, parent: QWidget):
        QWidget.__init__(self, parent)
        LogHelper.__init__(self)
        self.ui = Ui_TymboxAssistantView()
        self.ui.setupUi(self)
        self.assistant = None # type: TymboxAssistant

    def update(self):
        self.setVisible(self.assistant.current_task is not None)

        self.ui.editCurrentTaskName.setText(self.assistant.current_task_name.text())
        self.ui.editRemainingDuration.setText(self.assistant.remaining_time_action.text())

    def set_assistant(self, assistant: TymboxAssistant):
        self.assistant = assistant

        self.ui.btnEndCurrentTask.released.connect(self.assistant.end_current_task_action.trigger)
        self.assistant.current_task_name.changed.connect(self.update)
        self.assistant.remaining_time_action.changed.connect(self.update)

        self.update()

