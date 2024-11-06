import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpinBox, QPushButton, QCheckBox, QFormLayout)
from PyQt6.QtCore import QTimer, Qt
import pyautogui

class KeyListener(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkey_callback = None
        
    def nativeEvent(self, eventType, message):
        try:
            from ctypes import wintypes
            from ctypes import c_void_p, cast, POINTER
            if eventType == b"windows_generic_MSG":
                msg = wintypes.MSG.from_address(message.__int__())
                if msg.message == 0x0312:  # WM_HOTKEY
                    if self.hotkey_callback:
                        self.hotkey_callback()
                    return True, 0
        except:
            pass
        return False, 0

    def register_hotkey(self, callback):
        self.hotkey_callback = callback
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            # Register F6 as global hotkey (virtual key code 0x75)
            if not user32.RegisterHotKey(int(self.winId()), 1, 0, 0x75):
                print("Failed to register hotkey")
        except:
            print("Hotkey registration not supported on this platform")

class AutoClickerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoClicker")
        self.is_clicking = False
        
        # Create key listener
        self.key_listener = KeyListener()
        self.key_listener.register_hotkey(self.toggle_clicking)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Interval settings
        form_layout = QFormLayout()
        interval_layout = QHBoxLayout()
        
        self.hours_spinbox = QSpinBox()
        self.hours_spinbox.setRange(0, 23)
        self.hours_spinbox.setValue(0)
        interval_layout.addWidget(QLabel("Hours:"))
        interval_layout.addWidget(self.hours_spinbox)
        
        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setRange(0, 59)
        self.minutes_spinbox.setValue(0)
        interval_layout.addWidget(QLabel("Minutes:"))
        interval_layout.addWidget(self.minutes_spinbox)
        
        self.seconds_spinbox = QSpinBox()
        self.seconds_spinbox.setRange(0, 59)
        self.seconds_spinbox.setValue(1)
        interval_layout.addWidget(QLabel("Seconds:"))
        interval_layout.addWidget(self.seconds_spinbox)
        
        self.milliseconds_spinbox = QSpinBox()
        self.milliseconds_spinbox.setRange(0, 999)
        self.milliseconds_spinbox.setValue(0)
        interval_layout.addWidget(QLabel("Milliseconds:"))
        interval_layout.addWidget(self.milliseconds_spinbox)
        
        form_layout.addRow("Click Interval:", interval_layout)
        
        # Delay before starting
        delay_layout = QVBoxLayout()
        
        delay_minutes_layout = QHBoxLayout()
        self.delay_minutes_spinbox = QSpinBox()
        self.delay_minutes_spinbox.setRange(0, 59)
        self.delay_minutes_spinbox.setValue(0)
        delay_minutes_layout.addWidget(QLabel("Minutes:"))
        delay_minutes_layout.addWidget(self.delay_minutes_spinbox)
        
        delay_seconds_layout = QHBoxLayout()
        self.delay_seconds_spinbox = QSpinBox()
        self.delay_seconds_spinbox.setRange(0, 59)
        self.delay_seconds_spinbox.setValue(0)
        delay_seconds_layout.addWidget(QLabel("Seconds:"))
        delay_seconds_layout.addWidget(self.delay_seconds_spinbox)
        
        delay_layout.addLayout(delay_minutes_layout)
        delay_layout.addLayout(delay_seconds_layout)
        
        form_layout.addRow("Start Delay:", delay_layout)
        
        # Mouse button selection
        self.left_click_checkbox = QCheckBox("Left Click")
        self.left_click_checkbox.setChecked(True)
        self.left_click_checkbox.toggled.connect(self.on_left_click_toggled)
        self.right_click_checkbox = QCheckBox("Right Click")
        self.right_click_checkbox.toggled.connect(self.on_right_click_toggled)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.left_click_checkbox)
        button_layout.addWidget(self.right_click_checkbox)
        form_layout.addRow("Mouse Button:", button_layout)
        
        layout.addLayout(form_layout)
        
        # Start/Stop button
        self.toggle_button = QPushButton("Start (F6)")
        self.toggle_button.clicked.connect(self.toggle_clicking)
        layout.addWidget(self.toggle_button)
        
        # Setup timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_click)
        
        self.setFixedSize(700, 250)
    
    def on_left_click_toggled(self, checked):
        if checked:
            self.right_click_checkbox.setChecked(False)
    
    def on_right_click_toggled(self, checked):
        if checked:
            self.left_click_checkbox.setChecked(False)
    
    def toggle_clicking(self):
        self.is_clicking = not self.is_clicking
        if self.is_clicking:
            delay = (self.delay_minutes_spinbox.value() * 60000 +
                     self.delay_seconds_spinbox.value() * 1000)
            QTimer.singleShot(delay, self.start_clicking)
            self.toggle_button.setText("Stop (F6)")
        else:
            self.timer.stop()
            self.toggle_button.setText("Start (F6)")
    
    def start_clicking(self):
        interval = (self.hours_spinbox.value() * 3600000 +
                    self.minutes_spinbox.value() * 60000 +
                    self.seconds_spinbox.value() * 1000 +
                    self.milliseconds_spinbox.value())
        self.timer.start(interval)
    
    def perform_click(self):
        if self.left_click_checkbox.isChecked():
            pyautogui.click(button='left')
        elif self.right_click_checkbox.isChecked():
            pyautogui.click(button='right')
    
    def closeEvent(self, event):
        # Cleanup when window is closed
        try:
            import ctypes
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            user32.UnregisterHotKey(int(self.key_listener.winId()), 1)
        except:
            pass
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerWindow()
    window.show()
    sys.exit(app.exec())