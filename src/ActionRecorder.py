from PyQt6.QtCore import QThread, pyqtSignal
import pyautogui
import time

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