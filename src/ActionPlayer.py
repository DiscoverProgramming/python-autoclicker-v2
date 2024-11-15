from PyQt6.QtCore import QThread
import pyautogui
import time

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