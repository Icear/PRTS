import os
import time
import random
import re
import cv2 as cv
import numpy
import subprocess
import datetime
import logging
import sys
from ArknightsStatusChecker import ArknightsStatusChecker


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
        adb_prefix = ''  # prefix parameters

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
            self.logger.info(f"screen size is {screen_resolution.length}x{screen_resolution.width}")
            return screen_resolution

        def wait_for_device(self):
            self.logger.info('waiting for device...')
            os.system(f"{self.adb_path} {self.adb_prefix} wait-for-device")
            self.logger.info('device connected')

        def click(self, x, y):
            x = round(x, 0)
            y = round(y, 0)
            self.logger.info(f"tap({x}, {y})")
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
            # cv.line(image, (0, point_y),
            #         (image.shape[1], point_y), self.log_line_color, self.log_line_thickness)  # 画横线
            # cv.line(image, (point_x, 0), (point_x,
            #                               image.shape[0]), self.log_line_color, self.log_line_thickness)  # 画竖线
            # cv.putText(image, tag, (10, 120), self.log_font, self.log_text_scale,
            #            (255, 255, 255), 5, cv.LINE_AA)  # 打TAG
            cv.imwrite(os.path.join(self.log_path,
                                    f"log-{log_time.year}-{log_time.month}-{log_time.day}-{log_time.hour}"
                                    f"-{log_time.minute}-{log_time.second}-{tag}.png"), image)  # 保存

        def _delete_old_log(self):
            self.logger.info('clean log..')
            for file in os.listdir(self.log_path):
                os.remove(os.path.join(self.log_path, file))
            self.logger.info('log cleaned')

    logger = logging.getLogger('ArknightsAutoFighter')

    device_config = {
        'enter_team_up_x': 1851,
        'enter_team_up_x_prefix_start': 0,
        'enter_team_up_x_prefix_end': 210,
        'enter_team_up_y': 875,
        'enter_team_up_y_prefix_start': 0,
        'enter_team_up_y_prefix_end': 46,
        'enter_game_x': 1632,
        'enter_game_x_prefix_start': 0,
        'enter_game_x_prefix_end': 91,
        'enter_game_y': 534,
        'enter_game_y_prefix_start': 0,
        'enter_game_y_prefix_end': 54,
        'leave_settlement_x': 1615,
        'leave_settlement_x_prefix_start': 0,
        'leave_settlement_x_prefix_end': 148,
        'leave_settlement_y': 534,
        'leave_settlement_y_prefix_start': 0,
        'leave_settlement_y_prefix_end': 63,
        'leave_annihilation_settlement_x': 1615,
        'leave_annihilation_settlement_x_prefix_start': 0,
        'leave_annihilation_settlement_x_prefix_end': 148,
        'leave_annihilation_settlement_y': 534,
        'leave_annihilation_settlement_y_prefix_start': 0,
        'leave_annihilation_settlement_y_prefix_end': 63,
        'confirm_restore_mind_x': 1509,
        'confirm_restore_mind_x_prefix_start': 0,
        'confirm_restore_mind_x_prefix_end': 100,
        'confirm_restore_mind_y': 745,
        'confirm_restore_mind_y_prefix_start': 0,
        'confirm_restore_mind_y_prefix_end': 60,
        'screen_resolution': Screen(1920, 980),
    }

    status_checker = ArknightsStatusChecker()

    def __init__(self, fight_times, allow_use_medicine=False):
        """
        :param fight_times: 刷的次数，0为刷到体力不足
        :param allow_use_medicine:  是否允许使用回体力药剂
        """
        # 连接并初始化设备
        self.adb_controller = self.ADBController()
        # 初始化日志
        self.picture_logger = self.PictureLogger()
        # 获取设备分辨率
        self.target_resolution = self.device_config['screen_resolution']
        self.target_resolution = self.adb_controller.get_device_resolution()
        # 初始化统计变量
        self.fight_count = 0
        self.target_game_times = fight_times
        self.allow_use_medicine = allow_use_medicine

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
        # 循环调用auto_fight_once 来进行战斗
        self.logger.warning(f"start the {self.fight_count}/{self.target_game_times} fights")
        while self._auto_fight_once():
            self.fight_count += 1
            self.logger.warning(f"end the {self.fight_count}/{self.target_game_times} fights")
            if self.fight_count >= self.target_game_times != 0:
                # 次数达成，结束
                logging.info('finished')
                return
        if self.target_game_times != 0:
            # 非正常退出
            self.logger.error("fight finished with error")
            return
        self.logger.warning("finished")

    def _auto_fight_once(self):
        """
        进行一次自动战斗
        :return:  返回战斗是否成功，True 表示本次战斗成功且可进行下一次战斗，False表示战斗失败
        """
        # 调用status_checker确定当前状态，然后根据状态执行动作，不再为每个关卡指定时间定时
        fight_finished = False
        status = ''
        while True:
            last_status = status
            status = self.status_checker.check_status(self.adb_controller.get_device_screen_picture())
            if status == self.status_checker.ASC_STATUS_LEVEL_SELECTION:
                # 在关卡选择界面
                if fight_finished:
                    return True  # 战斗结束成功返回关卡选择界面，战斗结束
                # 尝试进入关卡选择界面
                self._enter_team_up()
                self._sleep(random.uniform(3, 5))  # 等待游戏响应
                continue
            if status == self.status_checker.ASC_STATUS_RESTORE_MIND_MEDICINE:
                # 在体力不足界面
                # 检查“允许使用体力药剂”标记，不允许则结束，允许则使用药剂
                if self.allow_use_medicine:
                    self.logger.warning('using medicine to restore mind as intend')
                    self._confirm_mind_restore()  # 使用体力药剂
                    self._sleep(random.uniform(3, 4))  # 等待游戏响应
                    continue
                self.logger.error(
                    f"can't continue due to bad status: {self.status_checker.ASC_STATUS_RESTORE_MIND_MEDICINE}")
                return False
            if status == self.status_checker.ASC_STATUS_RESTORE_MIND_STONE:
                # 在体力不足界面
                self.logger.error(
                    f"can't continue due to bad status: {self.status_checker.ASC_STATUS_RESTORE_MIND_MEDICINE}")
                return False
            if status == self.status_checker.ASC_STATUS_TEAM_UP:
                # 在队伍选择界面
                # 尝试进入战斗界面
                self._enter_game()
                self._sleep(random.uniform(3, 5))  # 等待游戏响应
                continue
            if status == self.status_checker.ASC_STATUS_FIGHTING:
                # 在战斗界面
                # 等待5秒后重新检查
                self._sleep(5)
                continue
            if status == self.status_checker.ASC_STATUS_ANNIHILATION_SETTLEMENT:
                # 在剿灭结算界面
                # 尝试离开剿灭结算页面
                self._leave_annihilation_settlement()
                self._sleep(random.uniform(1, 3))  # 等待游戏响应
                continue
            if status == self.status_checker.ASC_STATUS_BATTLE_SETTLEMENT:
                # 在战斗结算界面
                # 尝试离开结算页面
                self._leave_settlement()
                self._sleep(random.uniform(5, 8))  # 等待游戏响应
                # 一轮执行结束
                fight_finished = True
                continue
            if status == self.status_checker.ASC_STATUS_UNKNOWN:
                # 未知状态，等待五秒后再次检查
                if last_status == status:
                    # 连续2次检查失败则报错
                    self.logger.error(f"error, unrecognized status, check out log for screen shot")
                    self.picture_logger.log(1, 1, "unrecognized status for ArkngithsStatusChecker",
                                            self.adb_controller.get_device_screen_picture())
                    return False
                self._sleep(5)
                continue

    def _leave_settlement(self):
        """
        离开结算界面
        """
        point_x = self.device_config['leave_settlement_x'] - random.uniform(
            self.device_config['leave_settlement_x_prefix_start'],
            self.device_config['leave_settlement_x_prefix_end'])
        point_y = self.device_config['leave_settlement_y'] + random.uniform(
            self.device_config['leave_settlement_y_prefix_start'],
            self.device_config['leave_settlement_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)

        self.picture_logger.log(point_x, point_y, f"leave_settlement({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量

    def _leave_annihilation_settlement(self):
        """
        离开剿灭结算页面
        """
        point_x = self.device_config['leave_annihilation_settlement_x'] - random.uniform(
            self.device_config['leave_annihilation_settlement_x_prefix_start'],
            self.device_config['leave_annihilation_settlement_x_prefix_end'])
        point_y = self.device_config['leave_annihilation_settlement_y'] + random.uniform(
            self.device_config['leave_annihilation_settlement_y_prefix_start'],
            self.device_config['leave_annihilation_settlement_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        self.picture_logger.log(point_x, point_y, f"exit proxy fight result interface({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 剿灭系列结算需要多点击一次

    def _enter_game(self):
        """
        队伍选择界面进入游戏界面
        """
        point_x = self.device_config['enter_game_x'] - random.uniform(
            self.device_config['enter_game_x_prefix_start'],
            self.device_config['enter_game_x_prefix_end'])
        point_y = self.device_config['enter_game_y'] + random.uniform(
            self.device_config['enter_game_y_prefix_start'],
            self.device_config['enter_game_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        self.picture_logger.log(point_x, point_y, f"enter_game({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量

    def _enter_team_up(self):
        """
        从关卡选择界面进入队伍选择界面
        """

        point_x = self.device_config['enter_team_up_x'] - random.uniform(
            self.device_config['enter_team_up_x_prefix_start'],
            self.device_config['enter_team_up_x_prefix_end'])
        point_y = self.device_config['enter_team_up_y'] + random.uniform(
            self.device_config['enter_team_up_y_prefix_start'],
            self.device_config['enter_team_up_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        self.picture_logger.log(point_x, point_y, f"enter_team_up({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量

    def _confirm_mind_restore(self):
        """
        确认使用恢复药剂
        """
        point_x = self.device_config[''] - random.uniform(
            self.device_config['confirm_restore_mind_x_prefix_start'],
            self.device_config['confirm_restore_mind_x_prefix_end'])
        point_y = self.device_config['confirm_restore_mind_y'] + random.uniform(
            self.device_config['confirm_restore_mind_y_prefix_start'],
            self.device_config['confirm_restore_mind_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        self.picture_logger.log(point_x, point_y, f"confirm_restore_mind({point_x},{point_y})",
                                self.adb_controller.get_device_screen_picture())
        self.adb_controller.click(point_x, point_y)  # 点击时加上随机偏移量


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

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
    af = ArknightsAutoFighter(0)
    af.auto_fight()
