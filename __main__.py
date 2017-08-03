from PyQt5.QtGui import QIcon
from qtpy import QtCore

from Trello.AsyncTrelloClient import AsyncTrelloClient
from Views.Tymbox.MainWindow import MainWindow
from Trello.TrelloConfig import TrelloConfig
from PyQt5.QtWidgets import QApplication
import pyqttango
import sys
import ctypes
import colorama

def qt_message_handler(mode, context, message):
    if mode == QtCore.QtInfoMsg:
        mode = 'INFO'
    elif mode == QtCore.QtWarningMsg:
        mode = 'WARNING'
    elif mode == QtCore.QtCriticalMsg:
        mode = 'CRITICAL'
    elif mode == QtCore.QtFatalMsg:
        mode = 'FATAL'
    else:
        mode = 'DEBUG'
    print('qt_message_handler: line: %d, func: %s(), file: %s' % (
          context.line, context.function, context.file))
    print('  %s: %s\n' % (mode, message))

QtCore.qInstallMessageHandler(qt_message_handler)

def main():
    # Doesn't play well with pycharm console
    # colorama.init()
    app = QApplication(sys.argv)
    trello_client = AsyncTrelloClient(TrelloConfig(), app)
    wnd = MainWindow(trello_client)
    wnd.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
