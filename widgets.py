from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from collections import deque

class GraphWidget(QWidget):
    def __init__(self, title="", color=QColor(52, 152, 219)):
        super().__init__()
        self.title = title
        self.color = color
        self.data = deque([0] * 60, maxlen=60)
        self.setMinimumSize(200, 100)

    def update_data(self, value):
        self.data.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        for i in range(1, 4):
            y = int(h / 4 * i)
            painter.drawLine(0, y, w, y)
        
        if len(self.data) < 2: return
        
        path = QPolygonF()
        path.append(QPointF(0, h))
        step = w / 59
        for i, val in enumerate(self.data):
            path.append(QPointF(i * step, h - (val / 100 * h)))
        path.append(QPointF(w, h))
        
        fill_color = QColor(self.color); fill_color.setAlpha(40)
        painter.setBrush(QBrush(fill_color)); painter.setPen(Qt.NoPen)
        painter.drawPolygon(path)
        
        painter.setPen(QPen(self.color, 2)); painter.setBrush(Qt.NoBrush)
        for i in range(len(self.data) - 1):
            x1, y1 = i * step, h - (self.data[i] / 100 * h)
            x2, y2 = (i + 1) * step, h - (self.data[i+1] / 100 * h)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))