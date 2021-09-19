from abc import ABCMeta, abstractmethod


class Controller(metaclass=ABCMeta):

    @abstractmethod
    def get_device_screen_picture(self):
        pass

    @abstractmethod
    def get_device_resolution(self) -> (int, int):
        pass

    @abstractmethod
    def click(self, x, y):
        pass

    @abstractmethod
    def exec(self, command):
        pass
