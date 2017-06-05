from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QWidget

from AsyncTrelloClient import AsyncTrelloClient, AsyncTrelloWrapper
from TrelloBoardsModel import TrelloBoardsModel
from TrelloCardItemDelegate import TrelloCardItemDelegate
from TrelloCardsModel import TrelloCardsModel
from TrelloListsModel import TrelloListsModel
from TymboxModel import TymboxModel
from TymboxTaskDelegate import TymboxTaskDelegate
from TymboxTimeline import TymboxTimeline
from ui_TymBox import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self, trello_client: AsyncTrelloClient, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.trello_client = trello_client

        self.boards_model = TrelloBoardsModel(self.trello_client, self)
        self.boards_model.setObjectName("BoardsModel")

        self.lists_model = TrelloListsModel(self.trello_client, self)
        self.lists_model.setObjectName("ListsModel")

        self.cards_model = TrelloCardsModel(self)
        self.cards_model.setObjectName("CardsModel")

        self.tymbox_model = TymboxModel()
        self.tymbox_model.set_cards_model(self.cards_model)

        self.tymbox_timeline = None

        self.setup_ui()
        self.request_boards()

        default_card_mouse_event = self.ui.list_trello_cards.mouseMoveEvent
        default_card_leave_event = self.ui.list_trello_cards.leaveEvent

        def cardMouseEvent(*args, **kwargs):
            default_card_mouse_event(*args, **kwargs)
            self.ui.list_trello_cards.viewport().update()

        def cardLeaveEvent(*args, **kwargs):
            default_card_leave_event(*args, **kwargs)
            self.ui.list_trello_cards.viewport().update()

        self.ui.list_trello_cards.mouseMoveEvent = cardMouseEvent
        self.ui.list_trello_cards.leaveEvent = cardLeaveEvent

        """default_task_mouse_event = self.ui.tymbox_view.mouseMoveEvent
        default_task_leave_event = self.ui.tymbox_view.leaveEvent
        default_task_press_event = self.ui.tymbox_view.mousePressEvent

        def taskMoveEvent(*args, **kwargs):
            default_task_mouse_event(*args, **kwargs)
            self.ui.tymbox_view.viewport().update()

        def taskPressEvent(*args, **kwargs):
            default_task_press_event(*args, **kwargs)
            self.ui.tymbox_view.viewport().update()

        def taskLeaveEvent(*args, **kwargs):
            default_task_leave_event(*args, **kwargs)
            self.ui.tymbox_view.viewport().update()

        self.ui.tymbox_view.mouseMoveEvent = taskMoveEvent
        self.ui.tymbox_view.leaveEvent = taskLeaveEvent
        self.ui.tymbox_view.mousePressEvent = taskPressEvent
        """


    def retranslate_ui(self):
        self.ui.retranslateUi(self)

    def setup_ui(self):
        self.ui.setupUi(self)

        self.ui.cmb_boards.setModel(self.boards_model)
        self.ui.cmb_boards.setModelColumn(1)

        self.ui.cmb_lists.setModel(self.lists_model)
        self.ui.cmb_lists.setModelColumn(1)

        self.ui.list_trello_cards.setModel(self.cards_model)
        self.ui.list_trello_cards.setItemDelegate(TrelloCardItemDelegate(self.ui.list_trello_cards))

        """self.ui.tymbox_view.setModel(self.tymbox_model)
        self.ui.tymbox_view.setItemDelegate(TymboxTaskDelegate(self.ui.tymbox_view))"""

        self.tymbox_timeline = TymboxTimeline(self.tymbox_model)
        self.tymbox_timeline.setDelegate(TymboxTaskDelegate(self.tymbox_timeline))
        self.ui.tymbox_view.setWidget(self.tymbox_timeline)

        self.tymbox_timeline.setAcceptDrops(True)
        self.tymbox_timeline.setMouseTracking(True)

        self.ui.btn_refresh_boards.released.connect(self.request_boards)
        self.ui.btn_refresh_lists.released.connect(self.request_lists)

    def request_boards(self):
        self.ui.cmb_boards.clear()
        self.ui.cmb_boards.setEditable(True)
        self.ui.cmb_boards.setEnabled(False)
        self.ui.cmb_boards.setEditText("Fetching boards...")
        self.boards_model.request_boards()

    def request_lists(self):
        self.ui.cmb_lists.clear()
        self.ui.cmb_lists.setEditable(True)
        self.ui.cmb_lists.setEnabled(False)
        self.ui.cmb_lists.setEditText("Fetching lists...")

        selected_board_index = self.ui.cmb_boards.currentIndex()
        trello_board = self.boards_model.get_board(selected_board_index);
        self.lists_model.set_board(trello_board)

    @pyqtSlot(name="on_BoardsModel_modelReset")
    def on_board_model_reset(self):
        self.ui.cmb_boards.setEditable(False)
        self.ui.cmb_boards.setEnabled(True)

    @pyqtSlot(name="on_ListsModel_modelReset")
    def on_lists_model_reset(self):
        self.ui.cmb_lists.setEditable(False)
        self.ui.cmb_lists.setEnabled(True)

    @pyqtSlot(str, name="on_cmb_boards_activated")
    def on_board_selected(self, board_name):
        print("Selected board %s" % board_name)
        self.request_lists()

    @pyqtSlot(str, name="on_cmb_lists_activated")
    def on_list_selected(self, list_name):
        self.cards_model.set_list(AsyncTrelloWrapper(self.lists_model.get_list(self.ui.cmb_lists.currentIndex())))
        print("Selected list %s" % list_name)


