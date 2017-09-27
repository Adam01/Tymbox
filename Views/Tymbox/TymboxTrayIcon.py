from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QActionGroup, QSystemTrayIcon, QWidget

from Utils.LogHelper import LogHelper


class TymboxTrayIcon(QObject, LogHelper):
    def __init__(self, parent: QWidget, task_actions: QActionGroup):
        QObject.__init__(self, parent)
        LogHelper.__init__(self)

        self.tray_icon = QSystemTrayIcon(QIcon().fromTheme("appointment"), self)

        self.menu = QMenu(parent)

        self.tasks_sub_menu = QMenu(self.menu)
        self.tasks_sub_menu.setTitle("Current Task")
        self.tasks_sub_menu.addActions(task_actions.actions())

        self.menu.addMenu(self.tasks_sub_menu)


        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()


        self.tray_icon.activated.connect(self.on_activated)

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.Context:
            self.tasks_sub_menu.setVisible(self.tasks_sub_menu.actions()[0].isVisible())

