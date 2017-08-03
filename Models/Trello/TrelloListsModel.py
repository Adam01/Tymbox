import trello
from PyQt5.QtCore import QAbstractTableModel, pyqtSlot, QModelIndex, Qt

from Trello.AsyncTrelloClient import AsyncTrelloClient, AsyncTrelloWrapper


class TrelloListsModel(QAbstractTableModel):
    def __init__(self, trello_client: AsyncTrelloClient, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.trello_client = trello_client
        self.trello_board_lists = []
        self.trello_board = None

    def set_board(self, board: trello.Board):
        self.trello_board = AsyncTrelloWrapper(board)
        self.request_lists()

    def get_list(self, row) -> trello.List:
        return self.trello_board_lists[row]

    def get_column_data(self, row):
        trello_list = self.get_list(row)
        return [trello_list.id,
                trello_list.name,
                trello_list.board,
                trello_list.client,
                trello_list.closed,
                trello_list.pos]

    def request_lists(self):
        print("Fetching lists..")
        # noinspection PyArgumentList
        self.trello_board.all_lists(slot_callback=self.on_got_lists)

    @pyqtSlot(object, name="on_gotLists")
    def on_got_lists(self, list_list):
        self.beginResetModel()
        self.trello_board_lists = list_list
        print("Lists fetched. rowCount=%i, columnCount=%i" % (self.rowCount(), self.columnCount()))
        self.endResetModel()

    def data(self, index: QModelIndex, role=None):
        if not index.isValid() or index.row() >= self.rowCount() or index.column() >= self.columnCount():
            return None
        if role == Qt.DisplayRole:
            return str( self.get_column_data(index.row())[index.column()] )
        return None

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.trello_board_lists)

    def columnCount(self, parent=None, *args, **kwargs):
        return 6
