import datetime

import math
from types import SimpleNamespace
from typing import Union

from PyQt5.QtCore import QTimer, QRect, Qt, QModelIndex, pyqtSlot, QByteArray, QDataStream, QIODevice
from PyQt5.QtGui import QPaintEvent, QPainter, QDropEvent, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, \
    QMouseEvent, QPen, QColor, QShowEvent, QBrush
from PyQt5.QtWidgets import QWidget, QStyleOption, QStyleOptionViewItem, QSizePolicy

from Models.Tymbox.SequentialTymboxModel import SequentialTymboxModel
from Models.Tymbox.TymboxModel import TymboxModelColumns
from Utils.LogHelper import LogHelper
from Views.Tymbox.TymboxTaskView import TymboxTaskView


class TymboxTimeline(QWidget, LogHelper):

    def __init__(self, parent, model: SequentialTymboxModel):
        QWidget.__init__(self, parent)
        LogHelper.__init__(self, "TymboxTimeline")

        self.setFixedHeight(1000)
        self.setFixedWidth(100)
        self.tymbox_model = model

        self.zoom_level = 1
        self.pixels_minute = 1
        self.padding = SimpleNamespace(left=80, top=10, right=10, bottom=10)
        self.timeline_axis_offset = 75
        self.hour_time_marker_axis_offset = -15
        self.time_marker_axis_offset = -5
        self.hour_text_axis_offset = -55
        self.item_spacing = 2

        self.drop_y = None

        self.tymbox_model.rowsInserted.connect(self.on_rowsInserted)
        self.tymbox_model.durationChanged.connect(self.update_height)

    @pyqtSlot(QModelIndex, int, int)
    def on_rowsInserted(self, parent: QModelIndex, first: int, last: int):
        for i in range(first, last+1):
            self.log_extra_debug("Row inserted", row=i)
            TymboxTaskView(self, self.tymbox_model.index(i, 0))

    def showEvent(self, event: QShowEvent):
        QWidget.showEvent(self, event)
        self.setFixedWidth(self.parent().width())
        self.update_height(self.tymbox_model.duration)

    @pyqtSlot(int)
    def update_height(self, duration: int):
        duration_m = duration / 60
        self.setFixedHeight(duration_m * self.pixels_minute)
        self.log_extra_debug("Height set", height=duration_m * self.pixels_minute, duration=duration_m, pixels=self.pixels_minute)

    def paintEvent(self, paint_event: QPaintEvent):
        option = QStyleOptionViewItem()
        option.initFrom(self)
        option.rect.adjust(self.padding.left, self.padding.top, -self.padding.right, -self.padding.bottom)
        painter = QPainter(self)

        self.draw_current_time_indicator(option, painter)
        self.draw_timeline_axis(option, painter)
        self.draw_drop_zone(painter)

    def draw_drop_zone(self, painter: QPainter):
        if self.drop_y is not None:
            painter.fillRect(self.timeline_axis_offset,
                             self.drop_y,
                             self.width(),
                             self.pixels_minute*60,
                             QBrush(QColor(128,128,128,128)))

    def draw_current_time_indicator(self, option: QStyleOptionViewItem, painter: QPainter):
        start_time = self.tymbox_model.start_time
        current_time = datetime.datetime.today().timestamp()
        elapsed_time = current_time - start_time
        completion_y = int(elapsed_time / 60 * self.pixels_minute + option.rect.y())
        pen = painter.pen()
        pen.setColor(Qt.red)
        painter.setPen(pen)
        painter.drawLine(0, completion_y, self.width(), completion_y)

    def draw_timeline_axis(self, option: QStyleOptionViewItem, painter: QPainter):
        pen = painter.pen()
        pen.setColor(Qt.black)
        painter.setPen(pen)
        for i in range(0, self.height(), 15 * self.pixels_minute):
            y = i + option.rect.y()
            if i % (60 * self.pixels_minute) == 0:
                t = self.tymbox_model.start_time + (i / self.pixels_minute * 60)
                time = datetime.datetime.fromtimestamp(t).time()
                painter.drawLine(self.timeline_axis_offset + self.hour_time_marker_axis_offset, y,
                                 self.timeline_axis_offset, y)
                painter.drawText(self.timeline_axis_offset + self.hour_text_axis_offset, y, str(time))
            else:
                painter.drawLine(self.timeline_axis_offset + self.time_marker_axis_offset, y, self.timeline_axis_offset,
                                 y)

    def update_drop_zone(self, y):
        self.drop_y = self.snap_to_15mins(y)
        self.repaint()

    def clear_drop_zone(self):
        self.drop_y = None
        self.repaint()

    def dragEnterEvent(self, event: QDragEnterEvent):
        self.log_debug("Drag enter")
        event.acceptProposedAction()
        self.update_drop_zone(event.pos().y())

    def dragMoveEvent(self, event: QDragMoveEvent):
        # print("drag move")
        event.acceptProposedAction()
        self.update_drop_zone(event.pos().y())

    def setDragEnabled(self, enabled: bool):
        pass

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.log_debug("Drag leave")
        event.accept()
        self.clear_drop_zone()

    def snap_to_15mins(self, y) -> int:
        return y - (y-self.padding.top) % (self.pixels_minute*15)

    def get_time_from_offset(self, y) -> int:
        return self.tymbox_model.start_time + (self.snap_to_15mins(y)-self.padding.top) * self.pixels_minute*60

    def dropEvent(self, event: QDropEvent):
        self.clear_drop_zone()

        time = self.get_time_from_offset(event.pos().y())
        self.log_debug("Drop event", y=event.pos().y(), time=time)

        event.accept()

        mime_data = event.mimeData()

        byte_array = QByteArray()
        QDataStream(byte_array, QIODevice.WriteOnly).writeInt(time)
        mime_data.setData("application/tymbox-start-time", byte_array)

        if self.tymbox_model.canDropMimeData(mime_data, Qt.CopyAction, -1, -1, QModelIndex()):
            self.tymbox_model.dropMimeData(mime_data, Qt.CopyAction, -1, -1, QModelIndex())








