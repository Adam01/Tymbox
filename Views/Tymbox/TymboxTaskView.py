import math
from PyQt5.QtCore import QModelIndex, QPersistentModelIndex, pyqtSlot, Qt, QRect, pyqtSignal, QEvent
from PyQt5.QtGui import QCursor, QMouseEvent
from PyQt5.QtWidgets import QWidget, QDataWidgetMapper, QApplication

from Models.Tymbox.SequentialTymboxModel import SequentialTymboxModel
from Models.Tymbox.TymboxModel import TymboxModelColumns
from Utils.LogHelper import LogHelper, LogLevel
from Views.Generated.TymBoxTaskView import Ui_TymboxTaskView

class DragHelper(LogHelper):
    mouse_dragged = pyqtSignal(QModelIndex, int, name="mouseDragged")

    def __init__(self, widget, parent, cursor: QCursor, handler: callable, hot_spot: callable, name="DragHelper"):
        LogHelper.__init__(self, name)
        self.drag_last_pos = None
        self.widget = widget
        self.parent = parent
        self.cursor = cursor
        self.previous_cursor = None
        self.handler = handler
        self.hot_spot = hot_spot

        self.is_dragging = False
        self.is_over = False

    def prepare_drag(self):
        self.previous_cursor = self.parent.cursor()
        self.parent.setCursor(self.cursor)
        self.is_over = True

        self.log_debug("Prepped dragging")

    def start_drag(self, mouse_pos):
        self.parent.setDragEnabled(False)
        self.drag_last_pos = mouse_pos
        self.is_dragging = True

        self.log_debug("Started dragging")

    def end_drag(self):
        self.parent.setCursor(self.previous_cursor)
        self.parent.setDragEnabled(True)
        self.drag_last_pos = None
        self.is_dragging = False
        self.is_over = False

        self.log_debug("Stopped dragging")

    def check_dragging(self, rect_pos, event: QMouseEvent):
        mouse_pos = self.parent.mapFromGlobal(event.globalPos())
        left_mouse_down = QApplication.mouseButtons() & Qt.LeftButton
        drag_pos = self.hot_spot(rect_pos)

        if self.is_dragging:
            if left_mouse_down:
                if self.drag_last_pos != mouse_pos:

                    drag_distance = mouse_pos.y() - self.drag_last_pos.y()

                    if self.handler(drag_distance):
                        self.drag_last_pos = mouse_pos

            else:
                self.end_drag()

        elif drag_pos.contains(mouse_pos):
            self.log_extra_debug(widget=self.widget, widgetAt=QApplication.widgetAt(event.globalPos()))
            if not self.is_over:
                if not left_mouse_down and QApplication.widgetAt(event.globalPos()) == self.widget:
                    self.prepare_drag()
            elif QApplication.widgetAt(event.globalPos()) != self.widget:
                self.end_drag()
            elif left_mouse_down:
                self.start_drag(mouse_pos)
        else:
            if self.is_over:
                self.end_drag()

class TymboxTaskView(QWidget, LogHelper):
    def __init__(self, parent, index: QModelIndex):
        QWidget.__init__(self, parent)
        LogHelper.__init__(self, "TymboxTaskView(?)")
        self.set_log_level(LogLevel.Debug)
        self.ui = Ui_TymboxTaskView()
        self.setup_ui()
        self.model = index.model() # type: SequentialTymboxModel

        self.model.rowsAboutToBeRemoved.connect(self.on_rows_about_to_be_removed)
        self.model.dataChanged.connect(self.on_dataChanged)


        def start_hot_spot(rect_pos: QRect):
            return rect_pos.adjusted(0, 0, 0, -rect_pos.height() / 2)

        def duration_hot_spot(rect_pos: QRect):
            return rect_pos.adjusted(0, rect_pos.height()-4, 0, 0)

        self.start_timer_drag_helper = DragHelper(self, self.parent(), QCursor(Qt.SizeAllCursor), self.handle_start_time_drag, start_hot_spot)
        self.start_timer_drag_helper.set_log_name("StartDragHelper")
        self.start_timer_drag_helper.set_log_level(LogLevel.Info)


        self.duration_drag_helper = DragHelper(self, self.parent(), QCursor(Qt.SizeVerCursor), self.handle_duration_drag, duration_hot_spot)
        self.duration_drag_helper.set_log_name("DurationDragHelper")
        self.duration_drag_helper.set_log_level(LogLevel.Info)

        self.installEventFilter(self)
        self.setMouseTracking(True)
        self.parent().installEventFilter(self)
        for child in self.children():
            if isinstance(child, QWidget):
                child.installEventFilter(self)
                child.setMouseTracking(True)



        self.data_mapper = QDataWidgetMapper(self)
        self.data_mapper.setModel(self.model)

        self.data_mapper.addMapping(self.ui.lineEdit, TymboxModelColumns.name)

        self.data_mapper.setCurrentIndex(index.row())

        self.update_logging_name(self.model.get_event(self.data_mapper.currentIndex()).name)

        self.reposition()
        self.show()

    def setup_ui(self):
        self.ui.setupUi(self)

    def get_rect_rel_to_parent(self) -> QRect:
        rect = self.rect()
        pos = self.pos()
        rect = rect.adjusted(pos.x(), pos.y(), pos.x(), pos.y())
        return rect

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.MouseMove:
            this_rect = self.get_rect_rel_to_parent()
            self.start_timer_drag_helper.check_dragging(this_rect, event)
            self.duration_drag_helper.check_dragging(this_rect, event)
        return QWidget.eventFilter(self, obj, event)

    def update_logging_name(self, event_name):
        self.set_log_name("TymboxTaskView(%s)" % event_name)

    def reposition(self):
        event = self.model.get_event(self.data_mapper.currentIndex())

        from Views.Tymbox.TymboxTimeline import TymboxTimeline
        timeline = self.parent() # type: TymboxTimeline

        top_margin = timeline.item_spacing/2 if self.data_mapper.currentIndex() != 0 else 0
        bottom_margin = timeline.item_spacing/2 if self.data_mapper.currentIndex()+1 < self.model.rowCount() else 0

        duration_m = event.duration / 60
        start_time = event.start_time
        model_start_time = self.model.start_time
        item_height_pixels = timeline.pixels_minute * duration_m
        item_y_pixels = timeline.pixels_minute * (start_time - model_start_time) / 60
        x_pos = timeline.padding.left
        y_pos = timeline.padding.top + item_y_pixels + top_margin
        width = timeline.width() - timeline.padding.left - timeline.padding.right
        height = item_height_pixels - bottom_margin

        self.move(x_pos, y_pos)
        self.resize(width, height)

        self.log_debug("Repositioned", x=x_pos, y=y_pos, width=width, height=height)


    @pyqtSlot(QModelIndex, int, int)
    def on_rows_about_to_be_removed(self, index: QModelIndex, first: int, last: int):
        if first <= self.data_mapper.currentIndex() <= last:
            self.log_debug("Row removed from model, deleting...")
            self.deleteLater()

    def on_dataChanged(self, top_left: QModelIndex, bottom_right: QModelIndex, roles=None):
        if roles is None or Qt.EditRole in roles:
            if top_left.row() <= self.data_mapper.currentIndex() <= bottom_right.row():
                if top_left.column() <= TymboxModelColumns.name <= bottom_right.column():
                    self.update_logging_name(self.model.get_event(self.data_mapper.currentIndex()).name)

                if top_left.column() <= TymboxModelColumns.start_time <= bottom_right.column():
                    self.reposition()
                elif top_left.column() <= TymboxModelColumns.end_time <= bottom_right.column():
                    self.reposition()

    @pyqtSlot(name="on_btnRemove_released")
    def removeTask(self):
        self.log_debug("Remove requested")
        self.model.removeRow(self.data_mapper.currentIndex())

    def handle_start_time_drag(self, drag_distance: int) -> bool:

        pixels_minute = self.parent().pixels_minute
        minutes_dragged = drag_distance / pixels_minute
        start_time = self.model.get_event(self.data_mapper.currentIndex()).start_time
        new_start_time = start_time + minutes_dragged*60
        start_time_delta = new_start_time - start_time
        rounded_start_time = math.ceil(new_start_time/60 / 15) * 15*60 if start_time_delta < 0 else math.floor( new_start_time/60 / 15) * 15*60
        rounded_start_time_delta = int( rounded_start_time - start_time )

        self.log_extra_debug("Start time mouse drag",
                             pixel_distance=drag_distance,
                             minutes_dragged=minutes_dragged,
                             current_start_time=start_time,
                             new_start_time=new_start_time,
                             start_time_delta=start_time_delta,
                             rounded_start_time=rounded_start_time,
                             rounded_duration_delta=rounded_start_time_delta)

        if abs(rounded_start_time_delta) >= 15:
            # Drag in 15 minute increments
            new_start_time = self.model.alter_event_start_time(self.data_mapper.currentIndex(), rounded_start_time_delta)

            # Update preferred start to new value (if changed)
            self.model.setData(self.model.index(self.data_mapper.currentIndex(), TymboxModelColumns.preference_value), new_start_time)
            return True

        return False


    def handle_duration_drag(self, drag_distance: int) -> bool:
        pixels_minute = self.parent().pixels_minute
        minutes_dragged = drag_distance / pixels_minute
        duration_m = self.model.get_event(self.data_mapper.currentIndex()).duration/60
        new_duration_m = duration_m + minutes_dragged
        duration_delta = new_duration_m - duration_m
        rounded_duration = math.ceil(new_duration_m / 15) * 15 if duration_delta < 0 else math.floor(
            new_duration_m / 15) * 15
        rounded_duration_delta = rounded_duration - duration_m

        self.log_extra_debug("Duration mouse drag",
                             pixel_distance=drag_distance,
                             minutes_dragged=minutes_dragged,
                             current_duration=duration_m,
                             new_duration=new_duration_m,
                             duration_delta=duration_delta,
                             rounded_duration=rounded_duration,
                             rounded_duration_delta=rounded_duration_delta)

        if new_duration_m >=15 and abs(rounded_duration_delta) >= 15:
            # Drag in 15 minute increments
            self.model.alter_event_duration(self.data_mapper.currentIndex(), rounded_duration_delta*60 )
            return True

        return False

