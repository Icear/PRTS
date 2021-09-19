import logging

import win32gui

from controller.Controller import Controller


class WindowsAPIController(Controller):

    def __init__(self) -> None:
        self.logger = logging.getLogger('ADBController')
        win32gui.FindWindow()

    def get_device_screen_picture(self):
        pass

    def get_device_resolution(self):
        pass

    def click(self, x, y):
        pass

    def exec(self, command):
        pass
