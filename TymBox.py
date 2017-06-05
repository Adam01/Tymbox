from PyQt5.QtGui import QIcon
from AsyncTrelloClient import AsyncTrelloClient
from MainWindow import MainWindow
from TrelloConfig import TrelloConfig
from PyQt5.QtWidgets import QApplication
import pyqttango
import sys
import ctypes

def main():
    app = QApplication(sys.argv)
    trello_client = AsyncTrelloClient(TrelloConfig(), app)
    wnd = MainWindow(trello_client)
    wnd.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
