import datetime
import time

import math
from PyQt5.QtCore import QModelIndex, Qt, QSize, QPoint, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPalette, QColor, QCursor
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget, QApplication

from Models.Tymbox.TymboxModel import TymboxModelColumns
from Utils.LogHelper import LogHelper, LogLevel


class DragHelper(LogHelper):
    mouse_dragged = pyqtSignal(QModelIndex, int, name="mouseDragged")

    def __init__(self, parent, cursor: QCursor, handler: callable, hot_spot: callable):
        LogHelper.__init__(self)
        self.mouse_over_index = None
        self.drag_last_pos = None
        self.parent = parent
        self.cursor = cursor
        self.previous_cursor = None
        self.handler = handler
        self.hot_spot = hot_spot

    def prepare_drag(self, index: QModelIndex):
        self.previous_cursor = self.parent.cursor()
        self.parent.setCursor(self.cursor)
        self.mouse_over_index = index

    def start_drag(self, mouse_pos):
        self.parent.setDragEnabled(False)
        self.drag_last_pos = mouse_pos

    def end_drag(self):
        self.parent.setCursor(self.previous_cursor)
        self.parent.setDragEnabled(True)
        self.drag_last_pos = None
        self.mouse_over_index = None

    def check_dragging(self, index, rect_pos):
        mouse_pos = self.parent.mapFromGlobal(QCursor.pos())
        left_mouse_down = QApplication.mouseButtons() & Qt.LeftButton
        drag_pos = self.hot_spot(rect_pos)
        if self.mouse_over_index is not None:
            if self.mouse_over_index == index:
                if self.drag_last_pos is not None:
                    if left_mouse_down:
                        if self.drag_last_pos != mouse_pos:

                            drag_distance = mouse_pos.y() - self.drag_last_pos.y()

                            if self.handler(index, drag_distance):
                                self.drag_last_pos = mouse_pos

                        else:
                            # Not dragged
                            pass
                    else:
                        self.log_debug("Stopped dragging")
                        self.end_drag()
                else:
                    if left_mouse_down:
                        self.log_debug("Started dragging")
                        self.start_drag(mouse_pos)
                    else:
                        if not drag_pos.contains(mouse_pos):
                            # Mouse left drag area
                            self.log_extra_debug("Mouse left drag area")
                            self.end_drag()
                        else:
                            # Wait for mouse press
                            pass
            else:
                # Mouse somewhere else
                pass
        else:
            if left_mouse_down:
                # Mouse is already down, bail
                pass
            else:
                # Mouse is free to grab
                if drag_pos.contains(mouse_pos):
                    # Prepare drag
                    self.log_extra_debug("Prepped mouse for drag")
                    self.prepare_drag(index)
                else:
                    # Mouse not for dragging
                    pass


class TymboxTaskDelegate(QStyledItemDelegate, LogHelper):

    def __init__(self, parent: QWidget=None):
        QStyledItemDelegate.__init__(self, parent)
        self.vertical_spacing = 2

        def start_hot_spot(rect_pos: QRect):
            return rect_pos.adjusted(0, 0, 0, -rect_pos.height() / 2)

        def duration_hot_spot(rect_pos: QRect):
            return rect_pos.adjusted(0, rect_pos.height()-4, 0, 0)

        self.start_timer_drag_helper = DragHelper(parent, QCursor(Qt.SizeAllCursor), self.handle_start_time_drag, start_hot_spot)
        self.start_timer_drag_helper.set_log_name("StartDragHelper")
        self.start_timer_drag_helper.set_log_level(LogLevel.Info)


        self.duration_drag_helper = DragHelper(parent, QCursor(Qt.SizeVerCursor), self.handle_duration_drag, duration_hot_spot)
        self.duration_drag_helper.set_log_name("DurationDragHelper")
        self.duration_drag_helper.set_log_level(LogLevel.Info)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(option.palette.color(QPalette.WindowText))

        rect_pos = option.rect.adjusted(0, self.vertical_spacing, 0, -self.vertical_spacing)
        mouse_pos = self.parent().mapFromGlobal(QCursor.pos())

        self.draw_card(index, mouse_pos, painter, rect_pos)

        self.start_timer_drag_helper.check_dragging(index, rect_pos)
        self.duration_drag_helper.check_dragging(index, rect_pos)

    def draw_card(self, index, mouse_pos, painter, rect_pos):
        mouse_over = rect_pos.contains(mouse_pos, False)
        mouse_over_color_adjust = 20 if mouse_over else 0
        bg_color = QColor(200 - mouse_over_color_adjust, 255,
                          220 - mouse_over_color_adjust) if index.row() % 2 else QColor(200 - mouse_over_color_adjust,
                                                                                        220 - mouse_over_color_adjust,
                                                                                        255)
        brush = painter.brush()
        brush.setColor(bg_color)
        painter.setBrush(brush)
        mouse_over_curl_adjust = 1 if mouse_over else 0
        point_list = list()
        point_list.append(QPoint(rect_pos.x(),
                                 rect_pos.y()))
        point_list.append(QPoint(rect_pos.x() + rect_pos.width(),
                                 rect_pos.y()))
        point_list.append(QPoint(rect_pos.x() + rect_pos.width() - mouse_over_curl_adjust,
                                 rect_pos.y() + rect_pos.height() - mouse_over_curl_adjust))
        point_list.append(QPoint(rect_pos.x(),
                                 rect_pos.y() + rect_pos.height()))
        point_list.append(QPoint(rect_pos.x(),
                                 rect_pos.y()))
        painter.drawPolygon(*point_list)

        font = painter.font()
        font.setPixelSize(15)
        # font.setUnderline(True)
        painter.setFont(font)

        data = index.model().data(index.sibling(index.row(), TymboxModelColumns.name), Qt.DisplayRole)
        painter.drawText(rect_pos.x() + 5,
                         rect_pos.y() + 5,
                         rect_pos.width(),
                         rect_pos.height() / 2,
                         Qt.AlignLeft | Qt.AlignTop,
                         data)

        font.setPixelSize(10)
        font.setBold(False)
        # font.setUnderline(False)
        painter.setFont(font)

        data = index.model().data(index.sibling(index.row(), TymboxModelColumns.type), Qt.DisplayRole)
        painter.drawText(rect_pos.x() + 5,
                         rect_pos.y() + 5 + 18,
                         rect_pos.width(),
                         rect_pos.height() / 2,
                         Qt.AlignLeft | Qt.AlignTop,
                         data)

    def handle_start_time_drag(self, index: QModelIndex, drag_distance: int):

        pixels_minute = self.parent().pixels_minute
        minutes_dragged = drag_distance / pixels_minute
        start_time = index.model().data(index.sibling(index.row(), TymboxModelColumns.start_time), Qt.EditRole)
        new_start_time = start_time + minutes_dragged*60
        start_time_delta = new_start_time - start_time
        rounded_start_time = math.ceil(new_start_time/60 / 15) * 15*60 if start_time_delta < 0 else math.floor( new_start_time/60 / 15) * 15*60
        rounded_start_time_delta = rounded_start_time - start_time

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
            new_start_time = index.model().alter_event_start_time(index.row(), rounded_start_time_delta)

            # Update preferred start to new value (if changed)
            index.model().setData(index.sibling(index.row(), TymboxModelColumns.preference_value), new_start_time)
            return True

        return False


    def handle_duration_drag(self, index: QModelIndex, drag_distance: int):
        pixels_minute = self.parent().pixels_minute
        minutes_dragged = drag_distance / pixels_minute
        duration_m = index.model().get_event(index.row()).duration/60
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
            index.model().alter_event_duration(index.row(), rounded_duration_delta*60 )
            return True

        return False

    def sizeHint(self, QStyleOptionViewItem, index: QModelIndex):
        duration_m = index.model().get_event(index).duration*60
        model_duration_m = index.model().duration*60
        height = self.parent().height()
        pixels_minute = height/model_duration_m
        item_pixels = pixels_minute*duration_m
        return QSize(self.parent().viewport().width(), item_pixels)




