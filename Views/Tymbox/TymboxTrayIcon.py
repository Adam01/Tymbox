from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QActionGroup, QSystemTrayIcon, QWidget

from Models.Tymbox.TymboxModel import TymboxTask
from Utils.LogHelper import LogHelper
from Utils.TymboxAssistant import TymboxAssistant


class TymboxTrayIcon(QObject, LogHelper):
    def __init__(self, parent: QWidget, tymbox_assistant: TymboxAssistant):
        QObject.__init__(self, parent)
        LogHelper.__init__(self, "TymboxTrayIcon")
        self.tymbox_assistant = tymbox_assistant

        self.tray_icon = QSystemTrayIcon(QIcon().fromTheme("appointment"), self)
        self.menu = QMenu(parent)

        self.setup_current_task_menu(self.tymbox_assistant.action_map)
        self.setup_add_task_menu(self.tymbox_assistant.action_map)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.on_activated)
        self.tymbox_assistant.task_ended.connect(self.on_task_ended)

    @pyqtSlot(TymboxTask, name="on_task_ended")
    def on_task_ended(self, task: TymboxTask):
        self.tray_icon.showMessage("Times up!", "%s has ended" % task.name)

    def setup_add_task_menu(self, actions_map):
        add_task_sub_menu = QMenu(self.menu)
        add_task_sub_menu.setTitle("Add Task")
        add_task_sub_menu.addActions(actions_map["Add Task"].actions())
        self.menu.addMenu(add_task_sub_menu)

    def setup_current_task_menu(self, actions_map):
        tasks_sub_menu = QMenu(self.menu)
        tasks_sub_menu.setTitle("Current Task")
        tasks_sub_menu.addActions(actions_map["Current Task"].actions())
        self.menu.addMenu(tasks_sub_menu)

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.Context:
            for action in self.menu.actions():
                menu = action.menu()
                if menu:
                    action.setVisible(not menu.isEmpty())
        elif reason == QSystemTrayIcon.Trigger:
            if self.tymbox_assistant.current_task is not None:
                msg = "Current Task: %s\nRemaining Time: %s" % (self.tymbox_assistant.current_task_name.text(),
                                                                self.tymbox_assistant.remaining_time_action.text())
            else:
                msg = "No tasks currently underway"
            self.tray_icon.showMessage("Tymbox", msg, QSystemTrayIcon.Information)

