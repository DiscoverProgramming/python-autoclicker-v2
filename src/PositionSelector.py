from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor

class PositionSelector(QWidget):
    position_selected = pyqtSignal(QPoint)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Position")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.showFullScreen()  # Display the window in fullscreen mode

    def paintEvent(self, event):
        painter = QPainter(self)
        # Choose your desired color and transparency (alpha)
        # Example: Semi-transparent gray
        color = QColor(128, 128, 128, 100)  # RGB: Gray, Alpha: 100/255
        painter.fillRect(self.rect(), color)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Emit the global position where the user clicked
            self.position_selected.emit(event.globalPosition().toPoint())
            self.close()