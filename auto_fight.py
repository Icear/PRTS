import os
import time
import random
import re
import cv2 as cv
import numpy
import subprocess
import datetime
import logging


# from ArknightsStatusChecker import ArknightsStatusChecker


# TODO 整合StatusChecker


class ArknightsAutoFighter:
    class Screen:
        def __init__(self, length_x, width_y):
            self.length = int(length_x)
            self.width = int(width_y)
            if self.length < self.width:
                self.length, self.width = self.width, self.length

    class ADBController:
        logger = logging.getLogger('ADBController')
        adb_path = 'adb'
        adb_prefix = ''  # prefix paramater

        def __init__(self):
            os.system(f"{self.adb_path} kill-server")
            os.system(f"{self.adb_path} connect 127.0.0.1:7555")
            self.adb_prefix = '-s 127.0.0.1:7555'
            self.wait_for_device()

        def get_device_screen_picture(self):
            with subprocess.Popen(f"{self.adb_path} {self.adb_prefix} exec-out screencap -p", shell=True,
                                  stdout=subprocess.PIPE) as pip:
                data = pip.stdout.read()
            return data

        def get_device_resolution(self):
            self.logger.info('getting device screen resolution')
            with os.popen(f"{self.adb_path} {self.adb_prefix} shell wm size") as reply:
                pattern = re.compile(r'.*? (\d*?)x(\d*?)$')
                match_result = pattern.match(reply.readline())
                screen_resolution = ArknightsAutoFighter.Screen(match_result[1], match_result[2])
            self.logger.info('screen size is {screen_resolution.length}x{screen_resolution.width}')
            return screen_resolution

        def wait_for_device(self):
            self.logger.info('waiting for device...')
            os.system(f"{self.adb_path} {self.adb_prefix} wait-for-device")
            self.logger.info('device connected')

        def click(self, x, y):
            x = round(x, 0)
            y = round(y, 0)
            self.logger.info('tap({x}, {y})')
            os.system(f"{self.adb_path} {self.adb_prefix} shell input tap {x} {y}")

    class PictureLogger:
        logger = logging.getLogger('PictureLogger')
        log_delete_last = True
        log_path = os.path.join(os.getcwd(), 'log')
        log_line_color = (255, 0, 0)
        log_line_thickness = 2
        log_font = cv.FONT_HERSHEY_SIMPLEX
        log_text_scale = 2

        def __init__(self):
            # 清理日志
            if os.path.exists(self.log_path):
                if self.log_delete_last:
                    self._delete_old_log()
            else:
                os.mkdir(self.log_path)

        def log(self, point_x, point_y, tag, picture_data):
            log_time = datetime.datetime.now()
            image = cv.imdecode(numpy.frombuffer(
                picture_data, dtype="int8"), cv.IMREAD_UNCHANGED)
            cv.line(image, (0, point_y),
                    (image.shape[1], point_y), self.log_line_color, self.log_line_thickness)  # 画横线
            cv.line(image, (point_x, 0), (point_x,
                                          image.shape[0]), self.log_line_color, self.log_line_thickness)  # 画竖线
            cv.putText(image, tag, (10, 120), self.log_font, self.log_text_scale,
                       (255, 255, 255), 5, cv.LINE_AA)  # 打TAG
            cv.imwrite(os.path.join(self.log_path,
                                    f"log-{log_time.year}-{log_time.month}-{log_time.day}-{log_time.hour}"
                                    f"-{log_time.minute}-{log_time.second}-{tag}.png"), image)  # 保存

        def _delete_old_log(self):
            self.logger.info('clean log..')
            for file in os.listdir(self.log_path):
                os.remove(os.path.join(self.log_path, file))
            self.logger.info('log cleaned')

    logger = logging.getLogger('ArknightsAutoFighter')
    target_game_times = 7  # 要刷的次数
    target_game_name = '1-7'  # 要刷的关卡

    notify = False

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
            'enter_team_up_x': 2256,
            'enter_team_up_x_prefix_start': 0,
            'enter_team_up_x_prefix_end': 256,
            'enter_team_up_y': 965,
            'enter_team_up_y_prefix_start': 0,
            'enter_team_up_y_prefix_end': 50,
            'enter_game_x': 1990,
            'enter_game_x_prefix_start': 0,
            'enter_game_x_prefix_end': 110,
            'enter_game_y': 589,
            'enter_game_y_prefix_start': 0,
            'enter_game_y_prefix_end': 60,
            'leave_settlement_x': 1969,
            'leave_settlement_x_prefix_start': 0,
            'leave_settlement_x_prefix_end': 180,
            'leave_settlement_y': 589,
            'leave_settlement_y_prefix_start': 0,
            'leave_settlement_y_prefix_end': 70,
            'screen_resolution': Screen(2340, 1080)
        }
    }

    def __init__(self):
        # 连接并初始化设备
        self.adb_controller = self.ADBController()
        # 初始化日志
        self.picture_logger = self.PictureLogger()
        # 获取设备分辨率
        self.target_resolution = self.device_config['phone']['screen_resolution']
        self.target_resolution = self.adb_controller.get_device_resolution()

    @staticmethod
    def _compute_new_point(point_x, point_y, original_resolution, new_resolution):
        # 根据传入的原始分辨率和x,y坐标还有目标分辨率计算新的坐标位置
        new_x = point_x / original_resolution.length * new_resolution.length
        new_y = point_y / original_resolution.width * new_resolution.width
        return new_x, new_y

    @staticmethod
    def _sleep(fake_time):
        # a = 1
        time.sleep(fake_time)

    def auto_fight(self):
        # 在地图选择界面点击开始作战按钮
        self.logger.info("entering team up")
        self._enter_team_up()
        self._sleep(random.uniform(3, 5))

        # 选择队伍界面点击出战按钮
        self.logger.info('entering game...')
        self._enter_game()
        self._sleep(random.uniform(3, 5))

        # 等待游戏结束
        self.logger.info('start waiting for game finished')
        self.logger.info(' ')
        for j in range(self.time_dictionary[self.target_game_name]):
            self.logger.debug(f"waiting {j + 1} seconds for game finish...")
            self._sleep(1)
        self.logger.info('game finished')
        self._sleep(random.uniform(5, 8))

        # 退出结算界面
        self.logger.info('leaving the settlement interface...')
        self._leave_settlement()
        self._sleep(random.uniform(5, 8))

    '''
    离开结算界面
    '''

    def _leave_settlement(self):
        point_x = self.device_config['phone']['leave_settlement_x'] - random.uniform(
            self.device_config['phone']['leave_settlement_x_prefix_start'],
            self.device_config['phone']['leave_settlement_x_prefix_end'])
        point_y = self.device_config['phone']['leave_settlement_y'] + random.uniform(
            self.device_config['phone']['leave_settlement_y_prefix_start'],
            self.device_config['phone']['leave_settlement_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['phone']['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        if self.target_game_name[:1] == 'k':
            self.picture_logger.log(point_x, point_y, f"exit proxy fight result interface({point_x},{point_y})",
                                    self.adb_controller.get_device_screen_picture())
            self.adb_controller.click(point_x, point_y)  # 剿灭系列结算需要多点击一次
            self._sleep(random.uniform(1, 3))
        self.picture_logger.log(point_x, point_y, f"leave_settlement({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量

    '''
    从队伍选择界面进入游戏界面
    '''

    def _enter_game(self):
        point_x = self.device_config['phone']['enter_game_x'] - random.uniform(
            self.device_config['phone']['enter_game_x_prefix_start'],
            self.device_config['phone']['enter_game_x_prefix_end'])
        point_y = self.device_config['phone']['enter_game_y'] + random.uniform(
            self.device_config['phone']['enter_game_y_prefix_start'],
            self.device_config['phone']['enter_game_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['phone']['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        self.picture_logger.log(point_x, point_y, f"enter_game({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量

    '''
    从关卡选择界面进入队伍选择界面
    '''

    def _enter_team_up(self):
        point_x = self.device_config['phone']['enter_team_up_x'] - random.uniform(
            self.device_config['phone']['enter_team_up_x_prefix_start'],
            self.device_config['phone']['enter_team_up_x_prefix_end'])
        point_y = self.device_config['phone']['enter_team_up_y'] + random.uniform(
            self.device_config['phone']['enter_team_up_y_prefix_start'],
            self.device_config['phone']['enter_team_up_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['phone']['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        self.picture_logger.log(point_x, point_y, f"enter_team_up({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量


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
    af = ArknightsAutoFighter()
    print(
        f"target game is {af.target_game_name}, waiting time is {af.time_dictionary[af.target_game_name]}, "
        f"times is {af.target_game_times}, expected time consuming: "
        f"{af.target_game_times * af.time_dictionary[af.target_game_name]}s")

    for i in range(af.target_game_times):
        print(
            f"\n--------------------start the {i + 1}/{af.target_game_times} fights--------------------")
        af.auto_fight()
        print(
            f"--------------------end the {i + 1}/{af.target_game_times} fights----------------------\n")
