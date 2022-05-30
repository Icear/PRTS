import argparse
import datetime
import logging
import os
import random
import sys
import time

import cv2 as cv
import numpy

from statuschecker.TraditionalStatusChecker import TraditionalStatusChecker
from utils.controller import ADBController


class ArknightsAutoFighter:
    class SanityUsedUpException(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class StatusUnrecognizedException(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class Screen:
        def __init__(self, length_x, width_y):
            self.length = int(length_x)
            self.width = int(width_y)
            if self.length < self.width:
                self.length, self.width = self.width, self.length

    class PictureLogger:
        log_delete_last = False
        log_path = os.path.join(os.getcwd(), 'log', 'picture_log')
        log_line_color = (255, 0, 0)
        log_line_thickness = 2
        log_font = cv.FONT_HERSHEY_SIMPLEX
        log_text_scale = 2

        def __init__(self):
            self.logger = logging.getLogger('PictureLogger')

            # 清理日志
            if os.path.exists(self.log_path):
                if self.log_delete_last:
                    self._delete_old_log()
            else:
                os.makedirs(self.log_path)

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
        'leave_level_up_x': 1615,
        'leave_level_up_x_prefix_start': 0,
        'leave_level_up_x_prefix_end': 148,
        'leave_level_up_y': 534,
        'leave_level_up_y_prefix_start': 0,
        'leave_level_up_y_prefix_end': 63,
        'confirm_restore_sanity_x': 1509,
        'confirm_restore_sanity_x_prefix_start': 0,
        'confirm_restore_sanity_x_prefix_end': 100,
        'confirm_restore_sanity_y': 745,
        'confirm_restore_sanity_y_prefix_start': 0,
        'confirm_restore_sanity_y_prefix_end': 60,
        'screen_resolution': Screen(1920, 980),
        'menu_button_x': 364,
        'menu_button_y': 54,
        'home_button_x': 217,
        'home_button_y': 338,
        'mission_button_x': 1351,
        'mission_button_y': 812,
        'task_button_x': 1603,
        'task_button_y': 193,
        'confirm_retry_connection_x': 1108,
        'confirm_retry_connection_y': 618,
        'confirm_retry_connection_x_prefix_start': 0,
        'confirm_retry_connection_x_prefix_end': 450,
        'confirm_retry_connection_y_prefix_start': 0,
        'confirm_retry_connection_y_prefix_end': 100,
    }

    def __init__(self, fight_times, controller, allow_use_medicine=False):
        """
        :param fight_times: 刷的次数，0为刷到体力不足
        :param allow_use_medicine:  是否允许使用回体力药剂
        """
        self.logger = logging.getLogger('ArknightsAutoFighter')
        # 初始化StatusChecker
        self.status_checker = TraditionalStatusChecker()
        # 连接并初始化设备
        self.controller = controller
        # 初始化日志
        self.picture_logger = self.PictureLogger()
        # 获取设备分辨率
        self.target_resolution = self.device_config['screen_resolution']
        x, y = self.controller.get_device_resolution()
        self.target_resolution = self.Screen(x, y)
        # 初始化统计变量
        self.fight_count = 1
        self.target_game_times = int(fight_times)
        self.allow_use_medicine = bool(allow_use_medicine)

    @staticmethod
    def _compute_new_point(point_x, point_y, original_resolution, new_resolution):
        # 根据传入的原始分辨率和x,y坐标还有目标分辨率计算新的坐标位置
        new_x = point_x / original_resolution.length * new_resolution.length
        new_y = point_y / original_resolution.width * new_resolution.width
        return new_x, new_y

    @staticmethod
    def _sleep(fake_time):
        logging.debug(f"schedule sleep for {fake_time} seconds")
        logging.debug(f"start sleep: {time.ctime()}")
        # a = 1
        time.sleep(fake_time)
        logging.debug(f"end sleep: {time.ctime()}")

    def do_mission_complete(self):
        self.logger.info("do complete task")
        # self.adb_controller.click(self.device_config['menu_button_x'], self.device_config['menu_button_y'])
        self._sleep(10)
        self.controller.click(self.device_config['menu_button_x'], self.device_config['menu_button_y'])
        self._sleep(1)
        self.controller.click(self.device_config['home_button_x'], self.device_config['home_button_y'])
        self._sleep(4)
        self.controller.click(self.device_config['mission_button_x'], self.device_config['mission_button_y'])
        self._sleep(2)
        for i in range(24):
            self.controller.click(self.device_config['task_button_x'], self.device_config['task_button_y'])
            self._sleep(2)

    def auto_fight(self):
        # 循环调用auto_fight_once 来进行战斗
        # 退出情况有以下几种
        #   - 战斗次数结束退出（正常退出）
        #   - 理智耗尽退出（正常退出）
        #   - 无法识别状态退出（异常退出）
        self.logger.warning(
            f"start the {self.fight_count}/{self.target_game_times} fights")
        try:
            while self._auto_fight_once():
                self.logger.warning(
                    f"end the {self.fight_count}/{self.target_game_times} fights")
                self.fight_count += 1
                if (self.fight_count > self.target_game_times) and (self.target_game_times != 0):
                    # 次数达成，结束
                    self.logger.info('finished')
                    return True
        except ArknightsAutoFighter.SanityUsedUpException as sanity_used_up_exception:
            self.logger.error(sanity_used_up_exception)
            if self.target_game_times != 0:
                # 非正常退出
                self.logger.error("fight finished with error")
                raise sanity_used_up_exception
                # return False, sanity_used_up_exception
            return True
        except ArknightsAutoFighter.StatusUnrecognizedException as status_unrecognized_exception:
            self.logger.error(status_unrecognized_exception)
            raise status_unrecognized_exception
            # return False, status_unrecognized_exception

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
            screen_cap = self.controller.get_device_screen_picture()  # 取得截图
            status = self.status_checker.check_status(screen_cap)  # 检查状态
            self.picture_logger.log(-1, -1, status, screen_cap)

            if status == self.status_checker.ASC_STATUS_LEVEL_SELECTION:
                # 在关卡选择界面
                if fight_finished:
                    return True  # 战斗结束成功返回关卡选择界面，战斗结束
                # 尝试进入关卡选择界面
                self._enter_team_up()
                self._sleep(random.uniform(5, 9))  # 等待游戏响应
                continue
            if status == self.status_checker.ASC_STATUS_RESTORE_SANITY_MEDICINE:
                # 在体力不足界面
                # 检查“允许使用体力药剂”标记，不允许则结束，允许则使用药剂
                if self.allow_use_medicine:
                    self.logger.warning(
                        'using medicine to restore sanity as intend')
                    self._confirm_sanity_restore()  # 使用体力药剂
                    self._sleep(random.uniform(3, 4))  # 等待游戏响应
                    continue
                # return False
                raise ArknightsAutoFighter.SanityUsedUpException(
                    f"can't continue due to bad status: {self.status_checker.ASC_STATUS_RESTORE_SANITY_MEDICINE}")
            if status == self.status_checker.ASC_STATUS_RESTORE_SANITY_STONE:
                # 在体力不足界面
                # return False
                raise ArknightsAutoFighter.SanityUsedUpException(
                    f"can't continue due to bad status: {self.status_checker.ASC_STATUS_RESTORE_SANITY_MEDICINE}")
            if status == self.status_checker.ASC_STATUS_TEAM_UP:
                # 在队伍选择界面
                # 尝试进入战斗界面
                self._enter_game()
                self._sleep(random.uniform(15, 20))  # 等待游戏响应
                continue
            if status == self.status_checker.ASC_STATUS_FIGHTING:
                # 在战斗界面
                # 等待5秒后重新检查
                self._sleep(30)
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
            if status == self.status_checker.ASC_STATUS_LEVEL_UP:
                # 升级界面
                # 尝试离开升级界面
                self._leave_level_up_settlement()
                self._sleep(random.uniform(3, 5))  # 等待游戏响应
                continue
            if status == self.status_checker.ASC_STATUS_CONNECT_FAILED:
                self._retry_connection()
                self._sleep(random.uniform(5, 10))
            if status == self.status_checker.ASC_STATUS_UNKNOWN:
                # 未知状态，等待二十秒后再次检查
                self.picture_logger.log(1, 1, "unrecognized status for ArkngithsStatusChecker",
                                        screen_cap)
                if last_status == status:
                    # 连续2次检查失败则报错
                    raise ArknightsAutoFighter.StatusUnrecognizedException(
                        f"error, unrecognized status, check out log for screen shot")
                    # return False
                self._sleep(20)
                continue

    def _leave_settlement(self):
        """
        离开结算界面
        """
        point_x = self.device_config['leave_settlement_x'] + random.uniform(
            self.device_config['leave_settlement_x_prefix_start'],
            self.device_config['leave_settlement_x_prefix_end'])
        point_y = self.device_config['leave_settlement_y'] + random.uniform(
            self.device_config['leave_settlement_y_prefix_start'],
            self.device_config['leave_settlement_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)

        # self.picture_logger.log(point_x, point_y, f"leave_settlement({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)  # 点击时加上随机偏移量

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
        # self.picture_logger.log(point_x, point_y, f"exit_proxy_fight_result_interface({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)

    def _leave_level_up_settlement(self):
        """
        离开升级页面
        """
        point_x = self.device_config['leave_level_up_x'] - random.uniform(
            self.device_config['leave_level_up_x_prefix_start'],
            self.device_config['leave_level_up_x_prefix_end'])
        point_y = self.device_config['leave_level_up_y'] + random.uniform(
            self.device_config['leave_level_up_y_prefix_start'],
            self.device_config['leave_level_up_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        # self.picture_logger.log(point_x, point_y, f"exit_level_up_interface({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)

    def _retry_connection(self):
        """
        重新尝试连接
        """
        point_x = self.device_config['confirm_retry_connection_x'] - random.uniform(
            self.device_config['confirm_retry_connection_x_prefix_start'],
            self.device_config['confirm_retry_connection_x_prefix_end'])
        point_y = self.device_config['confirm_retry_connection_y'] + random.uniform(
            self.device_config['confirm_retry_connection_y_prefix_start'],
            self.device_config['confirm_retry_connection_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        # self.picture_logger.log(point_x, point_y, f"exit_level_up_interface({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)

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
        # self.picture_logger.log(point_x, point_y, f"enter_game({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)  # 点击时加上随机偏移量

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
        # self.picture_logger.log(point_x, point_y, f"enter_team_up({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)  # 点击时加上随机偏移量

    def _confirm_sanity_restore(self):
        """
        确认使用恢复药剂
        """
        point_x = self.device_config['confirm_restore_sanity_x'] - random.uniform(
            self.device_config['confirm_restore_sanity_x_prefix_start'],
            self.device_config['confirm_restore_sanity_x_prefix_end'])
        point_y = self.device_config['confirm_restore_sanity_y'] + random.uniform(
            self.device_config['confirm_restore_sanity_y_prefix_start'],
            self.device_config['confirm_restore_sanity_y_prefix_end'])
        point_x, point_y = self._compute_new_point(
            point_x, point_y, self.device_config['screen_resolution'], self.target_resolution)
        point_x = int(point_x)
        point_y = int(point_y)
        # self.picture_logger.log(point_x, point_y, f"confirm_restore_sanity({point_x},{point_y})",
        #                         self.adb_controller.get_device_screen_picture())
        self.controller.click(point_x, point_y)  # 点击时加上随机偏移量


# 启动参数
parser = argparse.ArgumentParser(description='Arkngihts auto fighter')
parser.add_argument('-t', '--times',
                    help='script run times, set 0 to unlimited run util sanity runs out, default 0 / '
                         '战斗次数，0表示刷至体力耗尽，默认为0',
                    type=int, default=0)
parser.add_argument('-m', '--medicine',
                    help='allow using medicine to restore sanity, default false / 允许使用体力药水来恢复体力，默认为否',
                    default=False, action='store_true')
parser.add_argument('-c', '--callback', help='the callback command to run after script finished / 程序完成后执行的回调命令')
parser.add_argument('-f', '--fallback',
                    help='the fallback command to run after script failed, support {} format for more detail')
parser.add_argument('-C', '--completetask', help='auto complete task after script finished / 程序完成后自动领取任务奖励',
                    default=False, action='store_true')
args = parser.parse_args()

if __name__ == '__main__':
    if not os.path.exists(os.path.join(os.getcwd(), 'log')):
        os.mkdir(os.path.join(os.getcwd(), 'log'))
        # 清理 log
    if os.path.exists(os.path.join(os.getcwd(), 'log', 'ArknightsAutoFighter.log')):
        os.remove(os.path.join(os.getcwd(), 'log', 'ArknightsAutoFighter.log'))
    # 设置写入 DEBUG 级 log 到文件
    logging.basicConfig(level=logging.DEBUG,
                        format=' %(asctime)s %(levelname)s: %(module)s: %(message)s',
                        datefmt='%Y/%m/%d %I:%M:%S %p',
                        filename=os.path.join(os.getcwd(), 'log', 'ArknightsAutoFighter.log')
                        )
    # 设置额外 handle 输出至 console，info 级别
    consoleLog = logging.StreamHandler(stream=sys.stdout)
    consoleLog.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt=' %(asctime)s %(levelname)s: %(module)s: %(message)s',
                                  datefmt='%Y/%m/%d %I:%M:%S %p')
    consoleLog.setFormatter(fmt=formatter)
    logging.getLogger().addHandler(consoleLog)

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

    if args.medicine:
        logging.warning("allow using medicine to restore sanity")
    else:
        logging.warning("disable using medicine")

    if args.completetask:
        logging.warning("will automatic finish task after script finish")

    if args.times != 0:
        logging.warning(f"fight times set to {args.times}")
    else:
        logging.warning(
            "unset fight times, script will keep running util sanity uses up")

    if args.callback:
        logging.warning(f"receive callback command:{args.callback}, recorded")

    if args.fallback:
        logging.warning(f"receive fallback command:{args.fallback}, recorded")
    auto_fighter = ArknightsAutoFighter(fight_times=args.times, controller=ADBController.ADBController(),
                                        allow_use_medicine=args.medicine)
    try:
        result = auto_fighter.auto_fight()
        # result = False
        if args.callback and result:
            logging.warning("executing callback command...")
            logging.warning(args.callback)
            output = os.system(args.callback)
            logging.warning(f"done, result: {output}")
        logging.info(f"final result is {result}")
    except ArknightsAutoFighter.SanityUsedUpException as e:
        if args.fallback:
            logging.warning("executing fallback command...")
            logging.warning(args.fallback.format(e))
            output = os.system(args.fallback.format(e))
            logging.warning(f"done, result: {output}")
    except ArknightsAutoFighter.StatusUnrecognizedException as e:
        if args.fallback:
            logging.warning("executing fallback command...")
            logging.warning(args.fallback.format(e))
            output = os.system(args.fallback.format(e))
            logging.warning(f"done, result: {output}")
        exit(-1)
    if args.completetask:
        auto_fighter.do_mission_complete()
