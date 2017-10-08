from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QActionGroup, QSystemTrayIcon, QWidget

from Utils.LogHelper import LogHelper


class TymboxTrayIcon(QObject, LogHelper):
    def __init__(self, parent: QWidget, actions_map: dict):
        QObject.__init__(self, parent)
        self.setObjectName("TymboxTrayIcon")
        LogHelper.__init__(self)

        self.tray_icon = QSystemTrayIcon(QIcon().fromTheme("appointment"), self)
        self.menu = QMenu(parent)

        self.setup_current_task_menu(actions_map)
        self.setup_add_task_menu(actions_map)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.on_activated)

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

