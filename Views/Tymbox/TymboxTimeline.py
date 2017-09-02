import datetime

import math
from PyQt5.QtCore import QTimer, QRect, Qt, QModelIndex, pyqtSlot
from PyQt5.QtGui import QPaintEvent, QPainter, QDropEvent, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, \
    QMouseEvent, QPen, QColor
from PyQt5.QtWidgets import QWidget, QStyleOption, QStyleOptionViewItem

from Models.Tymbox.SequentialTymboxModel import SequentialTymboxModel
from Models.Tymbox.TymboxModel import TymboxModelColumns
from Utils.LogHelper import LogHelper
from Views.Tymbox.TymboxTaskView import TymboxTaskView


class TymboxTimeline(QWidget, LogHelper):

    def __init__(self, parent, model: SequentialTymboxModel):
        QWidget.__init__(self, parent)
        LogHelper.__init__(self)
        self.zoom_level = 1
        self.setFixedHeight(1000)
        self.setFixedWidth(100)
        self.tymbox_model = model
        self.pixels_minute = 1

        self.tymbox_model.rowsInserted.connect(self.on_rowsInserted)

    @pyqtSlot(QModelIndex, int, int)
    def on_rowsInserted(self, parent: QModelIndex, first: int, last: int):
        for i in range(first, last+1):
            self.log_debug("Row inserted", row=i)
            TymboxTaskView(self, self.tymbox_model.index(i, 0))

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


    def dragEnterEvent(self, event: QDragEnterEvent):
        print("drag enter")
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        # print("drag move")
        event.acceptProposedAction()

    def setDragEnabled(self, enabled: bool):
        pass

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








