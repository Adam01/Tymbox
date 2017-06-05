from PyQt5.QtCore import QModelIndex, Qt, QSize, QPoint
from PyQt5.QtGui import QPainter, QPalette, QColor, QCursor
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

from TrelloCardsModel import TrelloCardsModelColumns


class TrelloCardItemDelegate(QStyledItemDelegate):

    def __init__(self, parent: QWidget=None):
        QStyledItemDelegate.__init__(self, parent)
        self.mouse_over = False

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(option.palette.color(QPalette.WindowText))

        rect_pos = option.rect.adjusted(0, 0, -5, -5)
        mouse_pos = self.parent().mapFromGlobal(QCursor.pos())
        mouse_over = rect_pos.contains(mouse_pos, False)

        mouse_over_color_adjust = 20 if mouse_over else 0
        bg_color = QColor(200 - mouse_over_color_adjust, 255, 220 - mouse_over_color_adjust) if index.row() % 2 else QColor(200 - mouse_over_color_adjust, 220 - mouse_over_color_adjust, 255)

        brush = painter.brush()
        brush.setColor(bg_color)
        painter.setBrush(brush)

        mouse_over_curl_adjust = 1 if mouse_over else 0

        point_list = list()
        point_list.append(QPoint(option.rect.x(),
                                 option.rect.y()))

        point_list.append(QPoint(option.rect.x() + option.rect.width()-5,
                                 option.rect.y()))

        point_list.append(QPoint(option.rect.x() + option.rect.width()-6 - mouse_over_curl_adjust,
                                 option.rect.y() + option.rect.height()-5 - mouse_over_curl_adjust))

        point_list.append(QPoint(option.rect.x(),
                                 option.rect.y() + option.rect.height() - 6))

        point_list.append(QPoint(option.rect.x(),
                                 option.rect.y()))

        painter.drawPolygon(*point_list)

        font = painter.font()
        font.setPixelSize(15)
        # font.setUnderline(True)
        painter.setFont(font)

        data = index.model().data(index.sibling(index.row(), TrelloCardsModelColumns.name), Qt.DisplayRole)
        painter.drawText(option.rect.x() + 5,
                         option.rect.y() + 5,
                         option.rect.width(),
                         option.rect.height() / 2,
                         Qt.AlignLeft | Qt.AlignTop,
                         data)

        # painter.drawLine(option.rect.x() + 5, option.rect.y()+5+17, option.rect.width()*3/4, option.rect.y()+5+17)

        font.setPixelSize(10)
        font.setBold(False)
        # font.setUnderline(False)
        painter.setFont(font)

        data = index.model().data(index.sibling(index.row(), TrelloCardsModelColumns.desc), Qt.DisplayRole)
        painter.drawText(option.rect.x()+5,
                         option.rect.y()+5 + 18,
                         option.rect.width(),
                         option.rect.height() / 2,
                         Qt.AlignLeft | Qt.AlignTop,
                         data)

    def sizeHint(self, QStyleOptionViewItem, QModelIndex):
        return QSize(200, 64)




