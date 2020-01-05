import os
import time
import random
import re
import cv2 as cv
import numpy
import subprocess
import datetime
from ArknightsStatusChecker import ArknightsStatusChecker


class Screen:
    def __init__(self, length_x, width_y):
        self.length = int(length_x)
        self.width = int(width_y)
        if self.length < self.width:
            self.length, self.width = self.width, self.length


target_game_times = 7   # 要刷的次数
target_game_name = '1-7'  # 要刷的关卡
notify = False

log_delete_last = True
log_path = os.path.join(os.getcwd(), 'log')
log_line_color = (255, 0, 0)
log_line_thickness = 2
log_font = cv.FONT_HERSHEY_SIMPLEX
log_text_scale = 2

adb_path = 'adb'
adb_prefix = ''  # prefix paramater
time_dictionary = {
    '1-7': 90,
    '2-10': 130,
    '3-1': 120,
    '3-2': 110,
    '3-3': 130,
    '3-4': 140,
    '3-7': 130,
    '3-8': 130,
    's4-1': 140,
    '4-6': 130,
    '5-7': 130,
    '5-10': 190,
    's3-3': 130,
    'ce-5': 130,
    'ls-5': 146,
    's2-6': 130,
    'ap-5': 140,
    'k-2': 853,
    'k-3': 885,
    'pr-a-1': 107,
    'pr-a-2': 130,
    'pr-b-2': 130,
    'pr-b-1': 130,
    'pr-c-1': 105,
    'pr-d-1': 130,
    'pr-d-2': 136,
    'of-8': 165,
    'of-7': 130,
    'of-6': 160,
    'of-f3': 130,
    'of-f4': 130
}  # 每个关卡的等待时间

device_config = {
    'phone': {
        'enter_company_interface_button_x': 2256,
        'enter_company_interface_button_x_prefix_start': 0,
        'enter_company_interface_button_x_prefix_end': 256,
        'enter_company_interface_button_y': 965,
        'enter_company_interface_button_y_prefix_start': 0,
        'enter_company_interface_button_y_prefix_end': 50,
        'enter_game_button_x': 1990,
        'enter_game_button_x_prefix_start': 0,
        'enter_game_button_x_prefix_end': 110,
        'enter_game_button_y': 589,
        'enter_game_button_y_prefix_start': 0,
        'enter_game_button_y_prefix_end': 60,
        'leave_summarize_interface_button_x': 1969,
        'leave_summarize_interface_button_x_prefix_start': 0,
        'leave_summarize_interface_button_x_prefix_end': 180,
        'leave_summarize_interface_button_y': 589,
        'leave_summarize_interface_button_y_prefix_start': 0,
        'leave_summarize_interface_button_y_prefix_end': 70,
        'screen_resolution': Screen(2340, 1080)
    }
}

target_resolution = device_config['phone']['screen_resolution']


def init():
    global adb_prefix
    os.system(f"{adb_path} kill-server")
    os.system(f"{adb_path} connect 127.0.0.1:7555")
    adb_prefix = '-s 127.0.0.1:7555'


def delete_old_log():
    print("clean log..", end='.')
    for file in os.listdir(log_path):
        os.remove(os.path.join(log_path, file))
    print("ok")


def log(point_x, point_y, tag):
    time = datetime.datetime.now()
    data = get_device_screen_picture()
    image = cv.imdecode(numpy.frombuffer(
        data, dtype="int8"), cv.IMREAD_UNCHANGED)
    # cv.line(image, (0, point_y),
    #         (image.shape[1], point_y), log_line_color, log_line_thickness)  # 画横线
    # cv.line(image, (point_x, 0), (point_x,
    #                               image.shape[0]), log_line_color, log_line_thickness)  # 画竖线
    # cv.putText(image, tag, (10, 120), log_font, log_text_scale,
    #            (255, 255, 255), 5, cv.LINE_AA)  # 打TAG
    cv.imwrite(os.path.join(log_path,f"log-{time.year}-{time.month}-{time.day}-{time.hour}-{time.minute}-{time.second}-{tag}.png"),
               image)  # 保存


def get_device_screen_picture():
    with subprocess.Popen(f"{adb_path} {adb_prefix} exec-out screencap -p", shell=True, stdout=subprocess.PIPE) as pip:
        data = pip.stdout.read()
    return data


def get_device_resolution():
    print("getting device screen resolution...", end='.')
    with os.popen(f"{adb_path} {adb_prefix} shell wm size") as reply:
        pattern = re.compile(r'.*? (\d*?)x(\d*?)$')
        match_result = pattern.match(reply.readline())
        screen_resolution = Screen(match_result[1], match_result[2])
    print(f"size is {screen_resolution.length}x{screen_resolution.width}")
    return screen_resolution


def compute_new_point(point_x, point_y, original_resoluton, new_resolution):
    # 根据传入的原始分辨率和x,y坐标还有目标分辨率计算新的坐标位置
    new_x = point_x / original_resoluton.length * new_resolution.length
    new_y = point_y / original_resoluton.width * new_resolution.width
    return new_x, new_y


def click(x, y):
    x = round(x, 0)
    y = round(y, 0)
    print(f"tap({x}, {y})")
    os.system(f"{adb_path} {adb_prefix} shell input tap {x} {y}")


def sleep(ftime):
    # a = 1
    time.sleep(ftime)


def wait_for_device():
    print("waiting for device...", end='.')
    os.system(f"{adb_path} {adb_prefix} wait-for-device")
    print("ok")


def auto_fight():
    # 在地图选择界面点击开始作战按钮
    print("entering interface...", end='.')
    point_x = device_config['phone']['enter_company_interface_button_x'] - random.uniform(
        device_config['phone']['enter_company_interface_button_x_prefix_start'],
        device_config['phone']['enter_company_interface_button_x_prefix_end'])
    point_y = device_config['phone']['enter_company_interface_button_y'] + random.uniform(
        device_config['phone']['enter_company_interface_button_y_prefix_start'],
        device_config['phone']['enter_company_interface_button_y_prefix_end'])
    point_x, point_y = compute_new_point(
        point_x, point_y, device_config['phone']['screen_resolution'], target_resolution)
    point_x = int(point_x)
    point_y = int(point_y)
    log(point_x, point_y, f"enter_company_interface({point_x},{point_y})")
    click(point_x, point_y)  # 点击时加上随机偏移量
    sleep(random.uniform(3, 5))
    # 选择队伍界面点击出战按钮
    print("entering game...", end='.')
    point_x = device_config['phone']['enter_game_button_x'] - random.uniform(
        device_config['phone']['enter_game_button_x_prefix_start'],
        device_config['phone']['enter_game_button_x_prefix_end'])
    point_y = device_config['phone']['enter_game_button_y'] + random.uniform(
        device_config['phone']['enter_game_button_y_prefix_start'],
        device_config['phone']['enter_game_button_y_prefix_end'])
    point_x, point_y = compute_new_point(
        point_x, point_y, device_config['phone']['screen_resolution'], target_resolution)
    point_x = int(point_x)
    point_y = int(point_y)
    log(point_x, point_y, f"enter_game({point_x},{point_y})")
    click(point_x, point_y)  # 点击时加上随机偏移量
    sleep(random.uniform(3, 5))
    # 等待游戏结束
    print(" ")
    for i in range(time_dictionary[target_game_name]):
        print(f"\rwaiting {i + 1} seconds for game finish...",
              end=".", flush=True)
        sleep(1)
    print("\rgame finished                                                ")
    sleep(random.uniform(5, 8))

    # 退出结算界面
    print("leaving the summarize interface...", end='.')
    point_x = device_config['phone']['leave_summarize_interface_button_x'] - random.uniform(
        device_config['phone']['leave_summarize_interface_button_x_prefix_start'],
        device_config['phone']['leave_summarize_interface_button_x_prefix_end'])
    point_y = device_config['phone']['leave_summarize_interface_button_y'] + random.uniform(
        device_config['phone']['leave_summarize_interface_button_y_prefix_start'],
        device_config['phone']['leave_summarize_interface_button_y_prefix_end'])
    point_x, point_y = compute_new_point(
        point_x, point_y, device_config['phone']['screen_resolution'], target_resolution)
    point_x = int(point_x)
    point_y = int(point_y)
    if target_game_name[0:1] == 'k':
        log(point_x, point_y, f"exit proxy fight result interface({point_x},{point_y})")
        click(point_x, point_y)  # 剿灭系列结算需要多点击一次
        sleep(random.uniform(1, 3))
    log(point_x, point_y, f"leave_summarize_interface({point_x},{point_y})")
    click(point_x, point_y)  # 点击时加上随机偏移量
    sleep(random.uniform(5, 8))


if __name__ == '__main__':

    print(
        '''
            _          _       _     _                         _         __ _       _     _
  __ _ _ __| | ___ __ (_) __ _| |__ | |_ ___        __ _ _   _| |_ ___  / _(_) __ _| |__ | |_
 / _` | '__| |/ / '_ \| |/ _` | '_ \| __/ __|_____ / _` | | | | __/ _ \| |_| |/ _` | '_ \| __|
| (_| | |  |   <| | | | | (_| | | | | |_\__ \_____| (_| | |_| | || (_) |  _| | (_| | | | | |_
 \__,_|_|  |_|\_\_| |_|_|\__, |_| |_|\__|___/      \__,_|\__,_|\__\___/|_| |_|\__, |_| |_|\__|
                         |___/                                                |___/
       '''
    )
    print(
        f"target game is {target_game_name}, waiting time is {time_dictionary[target_game_name]}, times is {target_game_times}, expected time consuming: {target_game_times * time_dictionary[target_game_name]}s")
    init()
    delete_old_log()
    wait_for_device()
    target_resolution = get_device_resolution()

    for i in range(target_game_times):
        print(
            f"\n--------------------start the {i + 1}/{target_game_times} fights--------------------")
        auto_fight()
        print(
            f"--------------------end the {i + 1}/{target_game_times} fights----------------------\n")

    print("program finished")
