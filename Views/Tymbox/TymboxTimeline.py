import datetime

import math
from PyQt5.QtCore import QTimer, QRect, Qt, QModelIndex
from PyQt5.QtGui import QPaintEvent, QPainter, QDropEvent, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, \
    QMouseEvent, QPen, QColor
from PyQt5.QtWidgets import QWidget, QStyleOption, QStyleOptionViewItem

from Models.Tymbox.TymboxModel import TymboxModelColumns


class TymboxTimeline(QWidget):

    def __init__(self, model):
        super().__init__(None)
        self.zoom_level = 1
        self.setFixedHeight(1000)
        self.setFixedWidth(100)
        self.tymbox_model = model
        self.task_delegate = None
        self.update_timer = QTimer(self)
        self.update_timer.setObjectName("update_timer")
        self.update_timer.setInterval(1000)
        self.update_timer.setSingleShot(False)
        self.update_timer.start()
        self.pixels_minute = 1

        self.update_timer.timeout.connect(self.update)

    def setDelegate(self, delegate):
        self.task_delegate = delegate

    def viewport(self):
        return self.parent()

    def paintEvent(self, paint_event: QPaintEvent):

        duration_m = self.tymbox_model.duration/60

        self.setFixedHeight(duration_m*self.pixels_minute)
        self.setFixedWidth(self.parent().width())

        option = QStyleOptionViewItem()
        option.initFrom(self)
        option.rect.adjust(80, 10, -10, -10)

        painter = QPainter(self)

        start_time = self.tymbox_model.start_time
        current_time = datetime.datetime.today().timestamp()
        elapsed_time = current_time - start_time
        completion_y = elapsed_time/60*self.pixels_minute + option.rect.y()

        pen = painter.pen()
        pen.setColor(Qt.red)
        painter.setPen(pen)
        painter.drawLine(60, completion_y, self.width(), completion_y)

        pen.setColor(Qt.black)
        painter.setPen(pen)

        for i in range(0, self.height(), 15*self.pixels_minute):
            y = i + option.rect.y()
            if i % (60*self.pixels_minute) == 0:
                t = self.tymbox_model.start_time + (i / self.pixels_minute * 60)
                time = datetime.datetime.fromtimestamp(t).time()
                painter.drawLine(60, y, 75, y)
                painter.drawText(20, y, str(time))
            else:
                painter.drawLine(70, y, 75, y)

        task_option = QStyleOptionViewItem()
        task_option.initFrom(self)
        for i in range(0, self.tymbox_model.rowCount()):
            index = self.tymbox_model.index(i, 0)
            task_option.rect = self.get_task_height(i)
            task_option.rect.adjust(option.rect.x(), option.rect.y(), option.rect.x()+option.rect.width(), option.rect.y())
            self.task_delegate.paint(painter, task_option, index)

    def get_task_height(self, row):
        event = self.tymbox_model.get_event(row)
        duration_m = event.duration/60
        start_time = event.start_time
        model_start_time = self.tymbox_model.start_time
        item_height_pixels = self.pixels_minute * duration_m
        item_y_pixels = self.pixels_minute * (start_time - model_start_time)/60
        return QRect(0, item_y_pixels, 0, item_height_pixels)



    def dragEnterEvent(self, event: QDragEnterEvent):
        print("drag enter")
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        # print("drag move")
        event.acceptProposedAction()
        self.update()

    def setDragEnabled(self, enabled: bool):
        pass

    def mouseMoveEvent(self, event: QMouseEvent):
        self.update()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        print("drag leave")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        print("drop event")
        event.accept()
        pos = event.pos()
        print(pos.x(), pos.y())
        option = QStyleOptionViewItem()
        option.initFrom(self)
        drop_index = QModelIndex()
        for i in range(0, self.tymbox_model.rowCount()):
            index = self.tymbox_model.index(i, 0)
            size = self.task_delegate.sizeHint(option, index)
            option.rect.setHeight(size.height())
            option.rect.setWidth(self.width())
            if option.rect.y() <= pos.y() <= (option.rect.y() + option.rect.height()):
                print("found drop target")
                drop_index = index
                break

            option.rect.adjust(0, size.height(), 0, 0)

        if self.tymbox_model.canDropMimeData(event.mimeData(), Qt.CopyAction, -1, -1, drop_index):
            self.tymbox_model.dropMimeData(event.mimeData(), Qt.CopyAction, -1, -1, drop_index)
            self.update()








