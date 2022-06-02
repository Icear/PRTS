import logging
import sys

import cv2 as cv
import numpy

from utils.controller import ADBController

"""
用于辅助获取点击区域
"""

flags = True
start_x = 0
start_y = 0
end_x = 0
end_y = 0


def cut(event, x, y, flag, param):
    global flags, start_x, start_y, end_x, end_y
    if event == cv.EVENT_LBUTTONDOWN:
        if flags:
            start_x = x
            start_y = y
            flags = False
        else:
            end_x = x
            end_y = y
            flags = True


def generate_click_zone():
    screen_shot = adb.get_device_screen_picture()
    image = cv.imdecode(numpy.frombuffer(
        screen_shot, dtype="int8"), cv.IMREAD_UNCHANGED)
    cv.namedWindow('image_original', cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
    cv.setMouseCallback('image_original', cut)
    cv.imshow('image_original', image)
    cv.waitKey(0)
    print(f"start_x: {start_x}")
    print(f"start_y: {start_y}")
    print(f"end_x: {end_x}")
    print(f"end_y: {end_y}")
    print(f"ScreenResolution({screen_length}, {screen_width}), {start_x}, {start_y}, {end_x}, {end_y}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format=' %(asctime)s %(levelname)s: %(module)s: %(message)s',
                        datefmt='%Y/%m/%d %I:%M:%S %p',
                        stream=sys.stdout
                        )
    adb = ADBController.ADBController()
    adb.wait_for_device()
    screen_length, screen_width = adb.get_device_resolution()
    while True:
        generate_click_zone()
