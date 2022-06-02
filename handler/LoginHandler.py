import logging
import random

import utils
import utils.click
import utils.controller
import utils.ocr
from utils.click.ScrennClick import ScreenResolution


class LoginHandler:
    """
    处理从游戏更新页面一直到主界面的过程
    """

    def __init__(self):
        self.logger = logging.getLogger('LoginHandler')
        self.status_handler_map = utils.generate_status_handler_map(self)

    def can_handle(self) -> bool:
        return utils.roll_status(self, self.status_handler_map)

    def do_logic(self):
        utils.roll_status_and_checker(self, self.status_handler_map)

    @staticmethod
    def _status_update_finished() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['清除缓存', '网络检测'])

    @staticmethod
    def _handle_update_finished():
        # 点击任意位置
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 648, 310, 1366, 671
        )
        utils.sleep(random.uniform(3, 5))

    @staticmethod
    def _status_account_login() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['开始唤醒', '查看公告', '账号管理'])

    @staticmethod
    def _handle_account_login():
        # 点击开始唤醒
        utils.click.click_text_from_context('开始唤醒')
        utils.sleep(random.uniform(15, 30))  # 等待游戏响应

    @staticmethod
    def _status_daily_checkin_reward() -> bool:
        """
        每日签到，已经领取奖励的界面
        :return:
        """
        return utils.check_keywords_from_context(['今日配给'])

    @staticmethod
    def _handle_daily_checkin_reward():
        # 点今日配给
        utils.click.click_text_from_context('今日配给')

    @staticmethod
    def _status_daily_checkin() -> bool:
        """
        每日签到，主界面
        :return:
        """
        return utils.check_keywords_from_context(['已签到', '常规配给'])

    @staticmethod
    def _handle_daily_checkin():
        # 点击关闭
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 1837, 65, 1873, 102
        )
        utils.sleep(random.uniform(3, 6))

    @staticmethod
    def _status_announcement() -> bool:
        """
        公告界面
        :return:
        """
        return utils.check_keywords_from_context(['系统公告', '活动公告'])

    @staticmethod
    def _handle_announcement():
        # 点击关闭
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 1833, 62, 1869, 102
        )
        utils.sleep(random.uniform(3, 6))

    @staticmethod
    def _status_main_screen() -> bool:
        return utils.check_keywords_from_context(['终端', '仓库', '任务', '采购中心'])

    @staticmethod
    def _handle_main_screen():
        # 结束逻辑
        raise utils.LogicFinishedException()
