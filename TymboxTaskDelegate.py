import datetime
import time

import math
from PyQt5.QtCore import QModelIndex, Qt, QSize, QPoint
from PyQt5.QtGui import QPainter, QPalette, QColor, QCursor
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget, QApplication

from TymboxModel import TymboxModelColumns


class TymboxTaskDelegate(QStyledItemDelegate):

    mouse_over_index = None

    def __init__(self, parent: QWidget=None):
        QStyledItemDelegate.__init__(self, parent)
        self.mouse_over_index = None
        self.vertical_spacing = 4
        self.drag_last_pos = None

    def prepare_drag(self, index: QModelIndex):
        self.parent().setCursor(QCursor(Qt.SizeVerCursor))
        self.mouse_over_index = index

    def start_drag(self, mouse_pos):
        self.parent().setDragEnabled(False)
        self.drag_last_pos = mouse_pos

    def end_drag(self):
        self.parent().setCursor(QCursor(Qt.ArrowCursor))
        self.parent().setDragEnabled(True)
        self.drag_last_pos = None
        self.mouse_over_index = None

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):

        type = index.model().data(index.sibling(index.row(), TymboxModelColumns.type), Qt.DisplayRole)
        if type == "Gap":
            return

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(option.palette.color(QPalette.WindowText))

        rect_pos = option.rect.adjusted(0, 0, 0, -self.vertical_spacing)
        mouse_pos = self.parent().mapFromGlobal(QCursor.pos())
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



        left_mouse_down = QApplication.mouseButtons() & Qt.LeftButton
        drag_pos = rect_pos.adjusted(0, rect_pos.height()-self.vertical_spacing-2, 0, 0)

        if self.mouse_over_index is not None:
            if self.mouse_over_index == index:
                if self.drag_last_pos is not None:
                    if left_mouse_down:
                        if self.drag_last_pos != mouse_pos:
                            drag_distance = mouse_pos.y() - self.drag_last_pos.y()
                            pixels_minute = self.parent().pixels_minute
                            minutes_dragged = drag_distance/pixels_minute
                            duration = index.model().data(index.sibling(index.row(), TymboxModelColumns.duration),
                                                          Qt.DisplayRole)
                            new_duration = duration + minutes_dragged
                            duration_delta = new_duration - duration
                            rounded_duration = math.ceil(new_duration / 15) * 15 if duration_delta < 0 else math.floor(new_duration / 15) * 15
                            rounded_duration_delta = rounded_duration - duration

                            if new_duration < 15:
                                pass
                            elif abs(rounded_duration_delta) >= 15:
                                # Drag in 15 minute increments
                                index.model().alter_event_duration(index.row(), rounded_duration-duration)

                                self.drag_last_pos = mouse_pos

                        else:
                            # Not dragged
                            pass
                    else:
                        print("Stopped dragging")
                        self.end_drag()
                else:
                    if left_mouse_down:
                        print("Started dragging")
                        self.start_drag(mouse_pos)
                    else:
                        if not drag_pos.contains(mouse_pos):
                            # Mouse left drag area
                            print("Mouse left drag area")
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
                    print("Prepped mouse for drag")
                    self.prepare_drag(index)
                else:
                    # Mouse not for dragging
                    pass

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

        # painter.drawLine(rect_pos.x() + 5, rect_pos.y()+5+17, rect_pos.width()*3/4, rect_pos.y()+5+17)

        font.setPixelSize(10)
        font.setBold(False)
        # font.setUnderline(False)
        painter.setFont(font)

        data = index.model().data(index.sibling(index.row(), TymboxModelColumns.type), Qt.DisplayRole)
        painter.drawText(rect_pos.x()+5,
                         rect_pos.y()+5 + 18,
                         rect_pos.width(),
                         rect_pos.height() / 2,
                         Qt.AlignLeft | Qt.AlignTop,
                         data)

    def sizeHint(self, QStyleOptionViewItem, index: QModelIndex):
        duration = index.model().data(index.sibling(index.row(), TymboxModelColumns.duration), Qt.DisplayRole)
        model_duration = index.model().duration
        height = self.parent().height()
        pixels_minute = height/model_duration
        item_pixels = pixels_minute*duration
        return QSize(self.parent().viewport().width(), item_pixels)




