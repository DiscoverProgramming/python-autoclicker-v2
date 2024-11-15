import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                           QComboBox, QCheckBox, QGroupBox, QGridLayout, 
                           QStatusBar, QFileDialog, QMessageBox, 
                           QDialog, QFormLayout, QLineEdit, QRadioButton)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QSettings, QPoint
from PyQt6.QtGui import QKeySequence, QPainter, QColor
import pyautogui
import json
import time
import ctypes
from ctypes import wintypes

from KeyListener import KeyListener
from PositionSelector import PositionSelector
from ActionRecorder import ActionRecorder
from ActionPlayer import ActionPlayer
from SettingsWindow import SettingsWindow

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

        # Click type selection in a nested layout
        click_type_widget = QWidget()
        click_type_layout = QHBoxLayout(click_type_widget)
        click_type_layout.setContentsMargins(20, 0, 0, 0)

        click_type_label = QLabel("Click Type:")
        click_type_label.setMinimumWidth(85)
        self.click_type = QComboBox()
        self.click_type.addItems(["Single", "Double"])
        self.click_type.setToolTip("Select the click type")
        self.click_type.setMinimumWidth(70)

        click_type_layout.addWidget(click_type_label)
        click_type_layout.addWidget(self.click_type)
        click_type_layout.addStretch()

        options_layout.addWidget(mouse_button_widget)
        options_layout.addWidget(click_type_widget)
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

        # Repeat mode radio buttons
        self.repeat_until_stopped_radio = QRadioButton("Repeat until stopped")
        self.repeat_for_radio = QRadioButton("Repeat for:")
        self.repeat_until_stopped_radio.setChecked(True)
        self.repeat_until_stopped_radio.toggled.connect(self.toggle_repeat_mode)

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
        self.repeat_count.setEnabled(False)  # Disable by default

        repeat_count_layout.addWidget(count_label)
        repeat_count_layout.addWidget(self.repeat_count)
        repeat_count_layout.addStretch()

        # Add widgets to the main repeat layout
        repeat_layout.addWidget(self.repeat_until_stopped_radio, 0, 0)
        repeat_layout.addWidget(self.repeat_for_radio, 1, 0)
        repeat_layout.addWidget(repeat_count_widget, 2, 0)

        # Add vertical stretch at the bottom
        repeat_layout.setRowStretch(3, 1)

        repeat_group.setLayout(repeat_layout)

        # Click Position Group
        position_group = QGroupBox("Click Position")
        position_group.setMinimumWidth(200)
        position_layout = QVBoxLayout()
        position_layout.setSpacing(10)
        position_layout.setContentsMargins(10, 15, 10, 10)

        self.mouse_position_radio = QRadioButton("Mouse Position")
        self.mouse_position_radio.setChecked(True)
        self.custom_position_radio = QRadioButton("Custom Position")
        self.mouse_position_radio.toggled.connect(self.toggle_position_mode)

        position_layout.addWidget(self.mouse_position_radio)
        position_layout.addWidget(self.custom_position_radio)

        self.position_label = QLabel("Position: (X, Y)")
        self.position_label.setToolTip("Set the position for clicking")
        self.position_label.setMinimumWidth(150)

        self.position_button = QPushButton("Set Position")
        self.position_button.setToolTip("Set the position for clicking")
        self.position_button.setMinimumWidth(100)
        self.position_button.clicked.connect(self.set_position)
        self.position_button.setEnabled(False)  # Disable by default

        position_layout.addWidget(self.position_label)
        position_layout.addWidget(self.position_button)
        position_layout.addStretch()
        position_group.setLayout(position_layout)

        # Add Click Options, Click Repeat, Click Position, and Click Speed groups to second row layout
        second_row_layout.addWidget(options_group)
        second_row_layout.addWidget(repeat_group)
        second_row_layout.addWidget(position_group)

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

    def toggle_repeat_mode(self):
        if self.repeat_for_radio.isChecked():
            self.repeat_count.setEnabled(True)
        else:
            self.repeat_count.setEnabled(False)

    def perform_click(self):
        button = self.mouse_button.currentText().lower()
        clicks = 2 if self.click_type.currentText() == "Double" else 1
        
        if self.custom_position_radio.isChecked() and self.click_position:
            pyautogui.click(x=self.click_position[0], y=self.click_position[1], button=button, clicks=clicks)
        else:
            pyautogui.click(button=button, clicks=clicks)
        
        if self.repeat_for_radio.isChecked():
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

    def toggle_position_mode(self):
        if self.custom_position_radio.isChecked():
            self.position_button.setEnabled(True)
        else:
            self.position_button.setEnabled(False)
            self.click_position = None  # Use current mouse position

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerWindow()
    window.show()
    sys.exit(app.exec())