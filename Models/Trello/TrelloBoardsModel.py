import trello
from PyQt5.QtCore import QAbstractTableModel, pyqtSlot, QModelIndex, Qt

from Trello.AsyncTrelloClient import AsyncTrelloClient
from Utils.LogHelper import LogHelper


class TrelloBoardsModel(QAbstractTableModel, LogHelper):
    def __init__(self, trello_client: AsyncTrelloClient, parent=None):
        QAbstractTableModel.__init__(self, parent)
        LogHelper.__init__(self, "TrelloBoardsModel")
        self.trello_client = trello_client
        self.trello_boards = []

    def request_boards(self):
        print("Fetching boards...")
        # noinspection PyArgumentList
        self.trello_client.list_boards(slot_callback=self.on_got_boards)

    def get_board(self, row_number) -> trello.Board:
        return self.trello_boards[row_number]

    @pyqtSlot(object, name="on_gotBoards")
    def on_got_boards(self, board_list):
        if board_list is not None:
            self.beginResetModel()
            self.trello_boards = board_list
            print("Boards fetched. rowCount=%i" % self.rowCount())
            self.endResetModel()
        else:
            self.log_warning("Unable to fetch trello boards")

    def data(self, index: QModelIndex, role=None):
        if not index.isValid() or index.row() > self.rowCount() or index.column() > self.columnCount():
            return None
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.trello_boards[index.row()].id
            if index.column() == 1:
                return self.trello_boards[index.row()].name
        return None

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.trello_boards)

    def columnCount(self, parent=None, *args, **kwargs):
        return 2
