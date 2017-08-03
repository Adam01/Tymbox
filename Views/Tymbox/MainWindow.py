from PyQt5.QtCore import pyqtSlot, qDebug
from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QMessageBox

from Models.Tymbox.TymboxModel import TymboxTask
from Trello.AsyncTrelloClient import AsyncTrelloClient, AsyncTrelloWrapper
from Utils.LogHelper import LogLevel
from Models.Tymbox.SequentialTymboxModel import SequentialTymboxModel
from Models.Trello.TrelloBoardsModel import TrelloBoardsModel
from Utils.TymboxAssistant import TymboxAssistant
from Views.Trello.TrelloCardItemDelegate import TrelloCardItemDelegate
from Models.Trello.TrelloCardsModel import TrelloCardsModel
from Models.Trello.TrelloListsModel import TrelloListsModel
from Views.Tymbox.TymboxTaskDelegate import TymboxTaskDelegate
from Views.Tymbox.TymboxTimeline import TymboxTimeline
from Views.Generated.TymBox import Ui_MainWindow
from Views.Generated.DebugTableView import Ui_DebugTableWindow

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

        self.tymbox_model = SequentialTymboxModel()
        self.tymbox_model.setObjectName("TymboxModel")
        self.tymbox_model.set_cards_model(self.cards_model)
        self.tymbox_model.set_log_level(LogLevel.Debug)

        self.tymbox_assistant = TymboxAssistant(self, self.tymbox_model)
        self.tymbox_assistant.setObjectName("TymboxAssistant")
        self.tymbox_assistant.set_log_level(LogLevel.Debug)

        self.tymbox_timeline = None

        self.setup_ui()

        self.debug_table_view = QDialog(self)
        self.debug_table_view_ui = Ui_DebugTableWindow()
        self.debug_table_view_ui.setupUi(self.debug_table_view)
        self.debug_table_view_ui.debugTableView.setModel(self.tymbox_model)
        self.debug_table_view.show()

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

        self.tymbox_timeline = TymboxTimeline(self.tymbox_model)
        delegate = TymboxTaskDelegate(self.tymbox_timeline)
        delegate.set_log_level(LogLevel.Debug)
        self.tymbox_timeline.setDelegate(delegate)
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

    @pyqtSlot(TymboxTask, name="on_TymboxAssistant_taskEnded")
    def on_task_ended(self, task: TymboxTask):
        QMessageBox.information(self, "Time's up!", "Current task has ended")

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


