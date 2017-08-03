from enum import IntEnum

import trello
from PyQt5.QtCore import QAbstractTableModel, pyqtSlot, QModelIndex, Qt, QObject, QMimeData, QByteArray
import json

from Trello.AsyncTrelloClient import AsyncTrelloWrapper
from Models.ExtendableItemModel import ExtendableItemModel, ItemModelDataSetType


class TrelloCardsModelColumns(IntEnum):
    id = 0
    name = 1
    board = 2
    client = 3
    closed = 4
    pos = 5
    idBoard = 6
    idList = 7
    idLabels = 8
    idMembers = 9
    idShort = 10
    trello_list = 11
    create_date = 12
    creation_date = 13
    dateLastActivity = 14
    desc = 15
    due = 16
    label_ids = 17
    labels = 18
    shortUrl = 19
    url = 20


class TrelloCardsModel(ExtendableItemModel):
    def __init__(self, parent: QObject = None):
        ExtendableItemModel.__init__(self, parent)
        self.trello_cards = []
        self.trello_board = None
        self.list = None

        ds = self.add_data_set("TrelloCardsModelDS", self.trello_cards, ItemModelDataSetType.Obj, False)
        self.add_columns(TrelloCardsModelColumns, ds)

    def set_list(self, list: AsyncTrelloWrapper):
        self.list = list
        self.request_cards()

    def request_cards(self):
        print("Fetching cards for %s" % str(self.list.name))
        # noinspection PyArgumentList
        self.list.list_cards(slot_callback=self.on_got_cards)

    @pyqtSlot(object, name="on_gotCards")
    def on_got_cards(self, cards: list):
        self.beginResetModel()
        self.trello_cards.clear()
        self.trello_cards[0:0] = cards
        self.endResetModel()

        print("Cards fetched. rowCount=%i, columnCount=%i" % (self.rowCount(), self.columnCount()))

    def flags(self, index: QModelIndex):
        if index.isValid():
            return Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled | ExtendableItemModel.flags(self, index)
        else:
            return Qt.ItemIsDropEnabled | ExtendableItemModel.flags(self, index)

    def supportedDragActions(self):
        return Qt.CopyAction

    def get_card(self, row: int) -> trello.Card:
        return self.trello_cards[row]

    def get_card_by_id(self, card_id: str):
        for card in self.trello_cards:
            if card.id == card_id:
                return card
        return None

    def mimeData(self, index_list: list):
        mime_data = QMimeData()

        json_data = dict()
        json_data["dataType"] = "TrelloCardIds"
        json_data["TrelloCardIds"] = list()
        for index in index_list:
            if index.isValid():
                card = self.get_card(index.row())
                json_data["TrelloCardIds"].append(card.id)

        json_str = json.dumps(json_data)
        print("Exporting MIME: %s" % json_str)
        byte_array = QByteArray()
        byte_array.append(json_str)
        mime_data.setData("application/json", byte_array)

        return mime_data