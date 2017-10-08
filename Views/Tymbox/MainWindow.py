import json

import os
from PyQt5.QtCore import Qt

from PyQt5.QtCore import pyqtSlot, qDebug
from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QMessageBox, QFileDialog

from Models.Tymbox.TymboxModel import TymboxTask
from Trello.AsyncTrelloClient import AsyncTrelloClient, AsyncTrelloWrapper
from Trello.TrelloConfig import TrelloConfig
from Utils.LogHelper import LogLevel
from Models.Tymbox.SequentialTymboxModel import SequentialTymboxModel
from Models.Trello.TrelloBoardsModel import TrelloBoardsModel
from Utils.TymboxAssistant import TymboxAssistant
from Views.Trello.TrelloCardItemDelegate import TrelloCardItemDelegate
from Models.Trello.TrelloCardsModel import TrelloCardsModel
from Models.Trello.TrelloListsModel import TrelloListsModel
from Views.Tymbox.TymboxTimeline import TymboxTimeline
from Views.Generated.TymBox import Ui_MainWindow
from Views.Generated.DebugTableView import Ui_DebugTableWindow
from Views.Tymbox.TymboxTrayIcon import TymboxTrayIcon


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.trello_client = AsyncTrelloClient(self)

        self.boards_model = TrelloBoardsModel(self.trello_client, self)
        self.boards_model.setObjectName("BoardsModel")

        self.lists_model = TrelloListsModel(self.trello_client, self)
        self.lists_model.setObjectName("ListsModel")

        self.cards_model = TrelloCardsModel(self)
        self.cards_model.setObjectName("CardsModel")

        self.tymbox_model = SequentialTymboxModel()
        self.tymbox_model.setObjectName("TymboxModel")
        self.tymbox_model.set_cards_model(self.cards_model)
        self.tymbox_model.set_log_level(LogLevel.ExtraDebug)

        self.tymbox_assistant = TymboxAssistant(self, self.tymbox_model)
        self.tymbox_assistant.setObjectName("TymboxAssistant")
        self.tymbox_assistant.set_log_level(LogLevel.Debug)

        self.tray_icon = TymboxTrayIcon(self, dict(self.tymbox_assistant.action_map, **self.tymbox_model.action_map))

        self.tymbox_timeline = None

        self.setup_ui()

        self.debug_table_view = QDialog(self)
        self.debug_table_view_ui = Ui_DebugTableWindow()
        self.debug_table_view_ui.setupUi(self.debug_table_view)
        self.debug_table_view_ui.debugTableView.setModel(self.tymbox_model)
        self.debug_table_view.show()

        self.trello_client.config_updated.connect(self.request_boards)

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

        self.show()

        self.trello_config = None

        self.app_dir_name = os.path.join(os.getenv('LOCALAPPDATA'), "Tymbox")
        self.model_file_name = os.path.join(self.app_dir_name , "model.json")
        self.trello_config_file = os.path.join(self.app_dir_name, "trello.json")


        if self.import_model_from_file(self.model_file_name):
            print("Loaded from %s" % self.model_file_name)
        else:
            print("Failed to load from %s" % self.model_file_name)

        trello_config = TrelloConfig()
        if trello_config.load_from_file(self.trello_config_file):
            print("Loaded from %s" % self.trello_config_file)
            self.trello_client.setup_from_config(trello_config)
            self.ui.trello_stack.setCurrentIndex(0)
        else:
            print("Failed to load from %s" % self.trello_config_file)


    def on_exit(self):
        if self.export_model_to_file(self.model_file_name):
            print("Saved to %s" % self.model_file_name)
        else:
            print("Failed to save to %s" % self.model_file_name)

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

        self.tymbox_timeline = TymboxTimeline(self.tymbox_timeline, self.tymbox_model)
        self.ui.tymbox_view.setWidget(self.tymbox_timeline)

        self.tymbox_timeline.setAcceptDrops(True)
        self.tymbox_timeline.setMouseTracking(True)

        self.ui.btn_refresh_boards.released.connect(self.request_boards)
        self.ui.btn_refresh_lists.released.connect(self.request_lists)

        self.ui.assistantView.set_assistant(self.tymbox_assistant)

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

    @pyqtSlot(name="on_btnInsertTask_released")
    def on_show_insert_task(self):
        self.ui.btnAddTask.setText("Insert")
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.checkComeBack.setVisible(False)

    @pyqtSlot(name="on_btnAppendTask_released")
    def on_show_append_task(self):
        self.ui.btnAddTask.setText("Append")
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.checkComeBack.setVisible(False)

    @pyqtSlot(name="on_btnInterruptTask_released")
    def on_show_interrupt_task(self):
        self.ui.btnAddTask.setText("Interrupt")
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.checkComeBack.setVisible(True)

    @pyqtSlot(name="on_btnAddTask_released")
    def on_add_task(self):
        if self.ui.btnAddTask.text() == "Append":
            self.tymbox_model.append_task(self.ui.editTaskName.text(),
                                          self.ui.spinTaskDuration.value()*60)
        elif self.ui.btnAddTask.text() == "Insert":
            self.tymbox_model.insert_task_after_current(self.ui.editTaskName.text(),
                                                        self.ui.spinTaskDuration.value()*60)
        elif self.ui.btnAddTask.text() == "Interrupt":
            self.tymbox_model.interrupt_current_task(self.ui.editTaskName.text(),
                                                     self.ui.spinTaskDuration.value()*60,
                                                     self.ui.checkComeBack.isChecked())

        self.ui.editTaskName.clear()
        self.ui.spinTaskDuration.setValue(15)
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.checkComeBack.setChecked(False)

    @pyqtSlot(name="on_btnAddTaskBack_released")
    def on_back_to_tasks(self):
        self.ui.stackedWidget.setCurrentIndex(0)

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

    @pyqtSlot(name="on_btnImport_released")
    def on_import_tasks(self):
        file_name = QFileDialog.getOpenFileName(self, "Import tasks")[0]
        if self.import_model_from_file(file_name):
            QMessageBox.information(self, "Success", "Imported tasks")

    @pyqtSlot(name="on_btnExport_released")
    def on_export_tasks(self):
        file_name = QFileDialog.getSaveFileName(self, "Export tasks")[0]
        if self.export_model_to_file(file_name):
            QMessageBox.information(self, "Success", "Exported tasks")

    def import_model_from_file(self, file_name) -> bool:
        if file_name is not None and len(file_name):
            try:
                fp = open(file_name)
                data = json.load(fp)
                if data is not None:
                    self.tymbox_model.import_tasks(data, True)
                    return True
            except:
                pass
        return False

    def export_model_to_file(self, file_name):
        if file_name is not None and len(file_name):
            try:
                dir_name = os.path.dirname(file_name)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                fp = open(file_name, 'w')
                data = self.tymbox_model.export_tasks()
                json.dump(data, fp)
                fp.close()
                return True
            except:
                pass
        return False

    @pyqtSlot(name="on_btn_request_trello_auth_released")
    def on_request_trello_auth(self):
        self.trello_config = TrelloConfig()
        url = self.trello_config.request_oauth(self.ui.edit_trello_key.text(), self.ui.edit_trello_secret.text())

        import webbrowser
        webbrowser.open(url)

    @pyqtSlot(str, name="on_edit_trello_verifier_textEdited")
    def on_trello_verifier_edited(self, value):
        if self.trello_config:
            if self.trello_config.complete_oauth(value):
                self.trello_client.setup_from_config(self.trello_config)
                self.trello_config.save_to_file(self.trello_config_file)
                self.trello_config = None
                QMessageBox.information(self, "Success", "Trello authenticated")
                self.ui.trello_stack.setCurrentIndex(0)
            else:
                QMessageBox.information(self, "Failed", "Trello PIN didn't seem to work...")