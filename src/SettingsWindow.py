from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QApplication
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QKeySequence

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