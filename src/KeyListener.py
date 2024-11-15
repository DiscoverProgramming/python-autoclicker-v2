from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSettings
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