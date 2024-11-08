import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                           QComboBox, QCheckBox, QGroupBox, QGridLayout, 
                           QStatusBar, QSlider, QFileDialog, QMessageBox, 
                           QDialog, QFormLayout, QLineEdit)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QSettings, QPoint
from PyQt6.QtGui import QKeySequence, QGuiApplication, QPainter, QColor
import pyautogui
import json
import time
import ctypes
from ctypes import wintypes

class KeyListener(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkey_actions = {}
        self.registered_hotkeys = {}
        self.settings = QSettings("MyApp", "AutoClicker")

    def nativeEvent(self, eventType, message):
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312:  # WM_HOTKEY
                hotkey_id = msg.wParam
                if hotkey_id in self.hotkey_actions:
                    self.hotkey_actions[hotkey_id]()
                return True, 0
        except:
            pass
        return False, 0

    def register_hotkey(self, hotkey_id, key_code, modifiers, callback):
        self.hotkey_actions[hotkey_id] = callback
        try:
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            if not user32.RegisterHotKey(int(self.winId()), hotkey_id, modifiers, key_code):
                print(f"Failed to register hotkey ID {hotkey_id}")
            else:
                self.registered_hotkeys[hotkey_id] = (modifiers, key_code)
        except:
            print("Hotkey registration not supported on this platform")

    def unregister_hotkeys(self):
        try:
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            for hotkey_id in self.registered_hotkeys:
                user32.UnregisterHotKey(int(self.winId()), hotkey_id)
            self.registered_hotkeys.clear()
        except:
            pass

    def load_hotkeys(self):
        self.unregister_hotkeys()
        # Retrieve hotkeys from settings
        start_stop_key = self.settings.value("start_stop_hotkey", "F6")
        record_key = self.settings.value("record_hotkey", "F9")
        stop_record_key = self.settings.value("stop_record_hotkey", "F10")
        stop_play_key = self.settings.value("stop_play_hotkey", "F8")

        # Map key names to virtual key codes
        key_map = {
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
            "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
            "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
            "CTRL": 0x11, "SHIFT": 0x10, "ALT": 0x12
            # ...add more keys as needed...
        }

        # Helper function to parse hotkey string
        def parse_hotkey(hotkey_str):
            parts = hotkey_str.upper().split('+')
            modifiers = 0
            key_code = 0
            for part in parts:
                if part in key_map:
                    if part == "CTRL":
                        modifiers |= 0x0002  # MOD_CONTROL
                    elif part == "SHIFT":
                        modifiers |= 0x0004  # MOD_SHIFT
                    elif part == "ALT":
                        modifiers |= 0x0001  # MOD_ALT
                    else:
                        key_code = key_map.get(part, 0)
            return key_code, modifiers

        # Register hotkeys
        hk1_code, hk1_mod = parse_hotkey(start_stop_key)
        self.register_hotkey(1, hk1_code, hk1_mod, self.parent().toggle_clicking)

        hk2_code, hk2_mod = parse_hotkey(record_key)
        self.register_hotkey(2, hk2_code, hk2_mod, self.parent().start_recording)

        hk3_code, hk3_mod = parse_hotkey(stop_record_key)
        self.register_hotkey(3, hk3_code, hk3_mod, self.parent().stop_recording)

        hk4_code, hk4_mod = parse_hotkey(stop_play_key)
        self.register_hotkey(4, hk4_code, hk4_mod, self.parent().stop_playing)

class ActionRecorder(QThread):
    actions_recorded = pyqtSignal(list)

    def run(self):
        self.recorded_actions = []
        self.is_recording = True
        self.start_time = time.time()
        pyautogui.PAUSE = 0  # Disable pyautogui's pause between actions
        while self.is_recording:
            x, y = pyautogui.position()
            action = {
                'time': time.time() - self.start_time,
                'position': (x, y),
                'event_type': 'move'
            }
            self.recorded_actions.append(action)
            time.sleep(0.1)

    def stop(self):
        self.is_recording = False

class ActionPlayer(QThread):
    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.actions = actions

    def run(self):
        start_time = time.time()
        for action in self.actions:
            time_to_wait = action['time'] - (time.time() - start_time)
            if time_to_wait > 0:
                time.sleep(time_to_wait)
            x, y = action['position']
            pyautogui.moveTo(x, y)

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

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("MyApp", "AutoClicker")
        self.parent_window = parent

        layout = QFormLayout(self)

        # Hotkey Settings with Rebind Buttons
        self.hotkey_fields = {}

        # Define hotkeys
        self.hotkeys = {
            "Start/Stop Clicking Hotkey": "start_stop_hotkey",
            "Start Recording Hotkey": "record_hotkey",
            "Stop Recording Hotkey": "stop_record_hotkey",
            "Stop Playing Hotkey": "stop_play_hotkey"
        }

        for label_text, key in self.hotkeys.items():
            h_layout = QHBoxLayout()

            # Read-only QLineEdit
            line_edit = QLineEdit(self.settings.value(key, ""))
            line_edit.setReadOnly(True)
            h_layout.addWidget(line_edit)

            # Rebind Button
            rebind_button = QPushButton("Rebind Hotkey")
            rebind_button.clicked.connect(lambda checked, k=key, le=line_edit, btn=rebind_button: self.rebind_hotkey(k, le, btn))
            h_layout.addWidget(rebind_button)

            layout.addRow(QLabel(label_text + ":"), h_layout)
            self.hotkey_fields[key] = line_edit

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        reset_button = QPushButton("Reset to Default")
        reset_button.clicked.connect(self.reset_to_default)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(close_button)

        layout.addRow(button_layout)

        self.current_rebind = None  # To keep track of which hotkey is being rebound

    def rebind_hotkey(self, key, line_edit, button):
        if self.current_rebind:
            QMessageBox.warning(self, "Rebind in Progress", "Finish rebinding the current hotkey first.")
            return
        self.current_rebind = (key, line_edit, button)
        line_edit.clear()
        button.setText("Listening")
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, source, event):
        if self.current_rebind and event.type() == event.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            # Build hotkey string
            hotkey_parts = []
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                hotkey_parts.append("CTRL")
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                hotkey_parts.append("SHIFT")
            if modifiers & Qt.KeyboardModifier.AltModifier:
                hotkey_parts.append("ALT")
            key_name = QKeySequence(key).toString().upper()
            if key_name and key_name not in ["CTRL", "SHIFT", "ALT"]:
                hotkey_parts.append(key_name)
            hotkey_str = " + ".join(hotkey_parts)

            # Update the QLineEdit
            key, line_edit, button = self.current_rebind
            line_edit.setText(hotkey_str)
            self.settings.setValue(key, hotkey_str)

            # Reload hotkeys in KeyListener
            self.parent_window.key_listener.load_hotkeys()
            self.parent_window.update_toggle_button()

            # Reset the button
            button.setText("Rebind Hotkey")
            self.current_rebind = None
            QApplication.instance().removeEventFilter(self)
            return True
        return super().eventFilter(source, event)

    def save_settings(self):
        self.settings.sync()
        QMessageBox.information(self, "Settings Saved", "Hotkeys have been saved successfully.")

    def reset_to_default(self):
        for key in self.hotkeys.values():
            default = {
                "start_stop_hotkey": "F6",
                "record_hotkey": "F9",
                "stop_record_hotkey": "F10",
                "stop_play_hotkey": "F8"
            }.get(key, "")
            self.settings.setValue(key, default)
            self.hotkey_fields[key].setText(default)
        self.parent_window.key_listener.load_hotkeys()
        self.parent_window.update_toggle_button()
        QMessageBox.information(self, "Reset to Default", "Hotkeys have been reset to default.")

class AutoClickerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoClicker")
        self.is_clicking = False
        self.click_position = None  # Initialize click position

        self.key_listener = KeyListener(self)
        self.key_listener.load_hotkeys()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Top row with Click Intervals group
        top_layout = QHBoxLayout()

        # Click Intervals Group
        interval_group = QGroupBox("Click Intervals")
        interval_layout = QGridLayout()

        self.hours_spinbox = QSpinBox()
        self.hours_spinbox.setToolTip("Set the hours interval for clicking")
        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setToolTip("Set the minutes interval for clicking")
        self.seconds_spinbox = QSpinBox()
        self.seconds_spinbox.setToolTip("Set the seconds interval for clicking")
        self.milliseconds_spinbox = QSpinBox()
        self.milliseconds_spinbox.setToolTip("Set the milliseconds interval for clicking")

        for spinbox in [self.hours_spinbox, self.minutes_spinbox, 
                       self.seconds_spinbox, self.milliseconds_spinbox]:
            spinbox.setMinimumWidth(70)
            if spinbox == self.milliseconds_spinbox:
                spinbox.setRange(0, 999)
            else:
                spinbox.setRange(0, 59)

        interval_layout.addWidget(self.hours_spinbox, 0, 0)
        interval_layout.addWidget(QLabel("Hours"), 0, 1)
        interval_layout.addWidget(self.minutes_spinbox, 0, 2)
        interval_layout.addWidget(QLabel("Minutes"), 0, 3)
        interval_layout.addWidget(self.seconds_spinbox, 0, 4)
        interval_layout.addWidget(QLabel("Seconds"), 0, 5)
        interval_layout.addWidget(self.milliseconds_spinbox, 0, 6)
        interval_layout.addWidget(QLabel("Milliseconds"), 0, 7)

        interval_group.setLayout(interval_layout)

        # Add Click Intervals group to top layout
        top_layout.addWidget(interval_group)

        # Second row with Click Options, Click Repeat, Click Position, and Click Speed groups
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(10)

        # Click Options Group
        options_group = QGroupBox("Click Options")
        options_group.setMinimumWidth(200)
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        options_layout.setContentsMargins(10, 15, 10, 10)

        # Mouse button selection in a nested layout
        mouse_button_widget = QWidget()
        mouse_button_layout = QHBoxLayout(mouse_button_widget)
        mouse_button_layout.setContentsMargins(20, 0, 0, 0)

        button_label = QLabel("Mouse Button:")
        button_label.setMinimumWidth(85)
        self.mouse_button = QComboBox()
        self.mouse_button.addItems(["Left", "Right", "Middle"])
        self.mouse_button.setToolTip("Select the mouse button to click")
        self.mouse_button.setMinimumWidth(70)

        mouse_button_layout.addWidget(button_label)
        mouse_button_layout.addWidget(self.mouse_button)
        mouse_button_layout.addStretch()

        # Double click checkbox
        self.double_click_checkbox = QCheckBox("Enable Double Click")
        self.double_click_checkbox.setToolTip("Enable double clicking")
        self.double_click_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                padding: 2px;
            }
        """)

        options_layout.addWidget(self.double_click_checkbox)
        options_layout.addWidget(mouse_button_widget)
        options_layout.addStretch()
        options_group.setLayout(options_layout)

        # Click Repeat Group
        repeat_group = QGroupBox("Click Repeat")
        repeat_group.setMinimumWidth(200)  # Set minimum width

        from PyQt6.QtWidgets import QSizePolicy
        options_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        repeat_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        repeat_layout = QGridLayout()
        repeat_layout.setSpacing(10)
        repeat_layout.setContentsMargins(10, 15, 10, 10)

        # Checkbox with custom styling
        self.enable_repeat_checkbox = QCheckBox("Enable Repeat")
        self.enable_repeat_checkbox.setToolTip("Enable repeating clicks")
        self.enable_repeat_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                padding: 2px;
            }
        """)

        # Repeat count spinbox and label in a nested layout
        repeat_count_widget = QWidget()
        repeat_count_layout = QHBoxLayout(repeat_count_widget)
        repeat_count_layout.setContentsMargins(20, 0, 0, 0)  # Add left indent

        count_label = QLabel("Repeat Count:")
        count_label.setMinimumWidth(85)
        self.repeat_count = QSpinBox()
        self.repeat_count.setRange(1, 9999)
        self.repeat_count.setMinimumWidth(70)
        self.repeat_count.setToolTip("Set the number of times to repeat clicks")
        self.repeat_count.setStyleSheet("""
            QSpinBox {
                padding: 2px;
                background-color: #ffffff;
            }
        """)

        repeat_count_layout.addWidget(count_label)
        repeat_count_layout.addWidget(self.repeat_count)
        repeat_count_layout.addStretch()

        # Add widgets to the main repeat layout
        repeat_layout.addWidget(self.enable_repeat_checkbox, 0, 0)
        repeat_layout.addWidget(repeat_count_widget, 1, 0)

        # Add vertical stretch at the bottom
        repeat_layout.setRowStretch(2, 1)

        self.enable_repeat_checkbox.stateChanged.connect(self.toggle_repeat_count)
        repeat_group.setLayout(repeat_layout)

        # Click Position Group
        position_group = QGroupBox("Click Position")
        position_group.setMinimumWidth(200)
        position_layout = QVBoxLayout()
        position_layout.setSpacing(10)
        position_layout.setContentsMargins(10, 15, 10, 10)

        self.position_label = QLabel("Position: (X, Y)")
        self.position_label.setToolTip("Set the position for clicking")
        self.position_label.setMinimumWidth(150)

        self.position_button = QPushButton("Set Position")
        self.position_button.setToolTip("Set the position for clicking")
        self.position_button.setMinimumWidth(100)
        self.position_button.clicked.connect(self.set_position)

        position_layout.addWidget(self.position_label)
        position_layout.addWidget(self.position_button)
        position_layout.addStretch()
        position_group.setLayout(position_layout)

        # Click Speed Group
        speed_group = QGroupBox("Click Speed")
        speed_group.setMinimumWidth(200)
        speed_layout = QVBoxLayout()
        speed_layout.setSpacing(10)
        speed_layout.setContentsMargins(10, 15, 10, 10)

        self.speed_label = QLabel("Speed: Normal")
        self.speed_label.setToolTip("Set the speed for clicking")
        self.speed_label.setMinimumWidth(150)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setToolTip("Set the speed for clicking")
        self.speed_slider.setMinimumWidth(100)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.valueChanged.connect(self.update_speed_label)

        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addStretch()
        speed_group.setLayout(speed_layout)

        # Add Click Options, Click Repeat, Click Position, and Click Speed groups to second row layout
        second_row_layout.addWidget(options_group)
        second_row_layout.addWidget(repeat_group)
        second_row_layout.addWidget(position_group)
        second_row_layout.addWidget(speed_group)

        # Add layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addLayout(second_row_layout)

        # Start/Stop button
        self.toggle_button = QPushButton()
        self.update_toggle_button()
        self.toggle_button.clicked.connect(self.toggle_clicking)
        self.toggle_button.setMinimumHeight(40)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        self.toggle_button.setToolTip("Start or stop the auto-clicker")
        main_layout.addWidget(self.toggle_button)

        # Third row with Recording Controls
        recording_layout = QHBoxLayout()

        # Record Button
        self.record_button = QPushButton("Record Actions")
        self.record_button.clicked.connect(self.start_recording)
        self.record_button.setToolTip("Start recording mouse actions")
        recording_layout.addWidget(self.record_button)

        # Stop Recording Button
        self.stop_record_button = QPushButton("Stop Recording")
        self.stop_record_button.clicked.connect(self.stop_recording)
        self.stop_record_button.setToolTip("Stop recording mouse actions")
        self.stop_record_button.setEnabled(False)
        recording_layout.addWidget(self.stop_record_button)

        # Play Button
        self.play_button = QPushButton("Play Actions")
        self.play_button.clicked.connect(self.play_actions)
        self.play_button.setToolTip("Play the recorded actions")
        self.play_button.setEnabled(False)
        recording_layout.addWidget(self.play_button)

        # Save Button
        self.save_button = QPushButton("Save Actions")
        self.save_button.clicked.connect(self.save_actions)
        self.save_button.setToolTip("Save recorded actions to a file")
        self.save_button.setEnabled(False)
        recording_layout.addWidget(self.save_button)

        # Load Button
        self.load_button = QPushButton("Load Actions")
        self.load_button.clicked.connect(self.load_actions)
        self.load_button.setToolTip("Load actions from a file")
        recording_layout.addWidget(self.load_button)

        main_layout.addLayout(recording_layout)

        # Settings Button
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings)
        main_layout.addWidget(settings_button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_click)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.resize(600, 400)  # Increased height for better layout

        self.recorded_actions = []

    def update_toggle_button(self):
        start_stop_key = self.key_listener.settings.value("start_stop_hotkey", "F6")
        self.toggle_button.setText(f"Start Clicking ({start_stop_key})" if not self.is_clicking else f"Stop Clicking ({start_stop_key})")

    def set_position(self):
        self.overlay = PositionSelector()
        self.overlay.position_selected.connect(self.position_captured)
        self.overlay.show()

    def position_captured(self, point):
        self.click_position = (point.x(), point.y())
        self.position_label.setText(f"Position: ({point.x()}, {point.y()})")
        self.status_bar.showMessage(f"Position set to ({point.x()}, {point.y()})", 5000)

    def update_speed_label(self):
        speed = self.speed_slider.value()
        self.speed_label.setText(f"Speed: {speed}")

    def toggle_repeat_count(self, state):
        if state == Qt.CheckState.Checked.value:
            self.repeat_count.setEnabled(True)
        else:
            self.repeat_count.setEnabled(False)

    def perform_click(self):
        button = self.mouse_button.currentText().lower()
        clicks = 2 if self.double_click_checkbox.isChecked() else 1
        if hasattr(self, 'click_position') and self.click_position:
            pyautogui.click(x=self.click_position[0], y=self.click_position[1], button=button, clicks=clicks)
        else:
            pyautogui.click(button=button, clicks=clicks)
        
        if self.enable_repeat_checkbox.isChecked():
            self.click_count += 1
            if self.click_count >= self.repeat_count.value():
                self.timer.stop()
                self.toggle_button.setText(f"Start Clicking ({self.key_listener.settings.value('start_stop_hotkey', 'F6')})")
                self.is_clicking = False
                self.status_bar.showMessage("Clicking stopped after reaching repeat count", 5000)

    def toggle_clicking(self):
        self.is_clicking = not self.is_clicking
        if self.is_clicking:
            self.click_count = 0
            interval = (
                self.hours_spinbox.value() * 3600000 +
                self.minutes_spinbox.value() * 60000 +
                self.seconds_spinbox.value() * 1000 +
                self.milliseconds_spinbox.value()
            )
            if interval == 0:
                QMessageBox.warning(self, "Invalid Interval", "Click interval cannot be zero.")
                self.is_clicking = False
                return
            self.timer.start(interval)
            self.update_toggle_button()
            self.status_bar.showMessage("Auto-clicking started", 5000)
        else:
            self.timer.stop()
            self.update_toggle_button()
            self.status_bar.showMessage("Auto-clicking stopped", 5000)

    def start_recording(self):
        self.record_button.setEnabled(False)
        self.stop_record_button.setEnabled(True)
        self.status_bar.showMessage("Recording started...", 5000)
        self.recorder = ActionRecorder()
        self.recorder.actions_recorded.connect(self.recording_finished)
        self.recorder.start()

    def stop_recording(self):
        if hasattr(self, 'recorder'):
            self.recorder.stop()
            self.stop_record_button.setEnabled(False)
            self.record_button.setEnabled(True)
            self.status_bar.showMessage("Recording stopped", 5000)

    def recording_finished(self, actions):
        self.recorded_actions = actions
        self.record_button.setEnabled(True)
        self.stop_record_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.status_bar.showMessage("Recording finished", 5000)

    def play_actions(self):
        if not self.recorded_actions:
            QMessageBox.warning(self, "No Actions", "No recorded actions to play.")
            return
        self.status_bar.showMessage("Playing actions...", 5000)
        self.player = ActionPlayer(self.recorded_actions)
        self.player.start()

    def save_actions(self):
        if not self.recorded_actions:
            QMessageBox.warning(self, "No Actions", "No recorded actions to save.")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Actions", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'w') as f:
                json.dump(self.recorded_actions, f)
            self.status_bar.showMessage("Actions saved", 5000)

    def load_actions(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Actions", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as f:
                self.recorded_actions = json.load(f)
            self.play_button.setEnabled(True)
            self.save_button.setEnabled(True)
            self.status_bar.showMessage("Actions loaded", 5000)

    def open_settings(self):
        self.settings_window = SettingsWindow(self)
        self.settings_window.show()

    def stop_playing(self):
        if hasattr(self, 'player') and self.player.isRunning():
            self.player.terminate()
            self.status_bar.showMessage("Playback stopped", 5000)

    def closeEvent(self, event):
        self.key_listener.unregister_hotkeys()
        try:
            if hasattr(self, 'recorder') and self.recorder.isRunning():
                self.recorder.stop()
        except:
            pass
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerWindow()
    window.show()
    sys.exit(app.exec())