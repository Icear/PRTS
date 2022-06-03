import logging
import random

import utils
from utils.click import ScreenResolution


class TemporalEventHandler:
    """临时活动处理，主要是签到活动"""

    def __init__(self):
        self.logger = logging.getLogger('ArknightsAutoFighter')
        self.status_handler_map = utils.generate_status_handler_map(self)
        self.gift_received = False

    def can_handle(self) -> bool:
        return utils.roll_status(self, self.status_handler_map)

    def do_logic(self):
        utils.roll_status_and_checker(self, self.status_handler_map)

    @staticmethod
    def _status_sign_in_event():
        """端午签到活动，或者所有签到活动可能都行"""
        return utils.check_keywords_from_context(['签到活动'])

    def _handle_sign_in_event(self):

        if self.gift_received:
            # 该退出了，先重置标识符
            self.gift_received = False
            utils.click.click_from_context(
                ScreenResolution(1920, 1080), 1831, 134, 1869, 170
            )
            utils.sleep(random.uniform(2, 4))
            raise utils.LogicFinishedException()

        # 一般是第1、2、3这种天数的签到，所以一路遍历找对应数字然后全点一遍，触发礼物领取以后留个标记就可以退出了
        for day in range(15):
            if utils.check_keywords_from_context([str(day)]):
                # 找到确实有天数写在里面，那就全点一遍，防止出错
                utils.click.click_every_same_text_from_context(str(day))
                return

        # 如果完全没找到的话，就G了，请求介入把
        raise utils.StatusUnrecognizedException()

    @staticmethod
    def _status_gift_received():
        # TODO 补全检查条件
        return utils.check_keywords_from_context(['物资'])

    def _handle_gift_received(self):
        utils.click.click_text_from_context('物资')
        utils.sleep(random.uniform(2, 4))
        self.gift_received = True
