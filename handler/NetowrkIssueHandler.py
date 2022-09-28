import logging
import random

import utils.ocr
from context import Context
from utils.click import ScreenResolution


class NetworkIssueHandler:
    """ 用于处理网络连接问题的突发情况 """

    def __init__(self):
        self.status_handler_map = utils.generate_status_handler_map(self)
        self.logger = logging.getLogger('NetworkIssueHandler')
        # Context.register_value_change_callback(utils.ocr.CONTEXT_KEY_OCR_RESULT, self._handle_context_call_back)

    def _handle_context_call_back(self, key, value):
        # 检查value里是否包含关键词，出现的话就中止掉现在的逻辑，然后走正常流程让当前的Handler接管
        if key == utils.ocr.CONTEXT_KEY_OCR_RESULT:
            if Context.get_value(utils.CONTEXT_KEY_PRTS_CURRENT_HANDLE) == self:
                return
            # 如果当前没有handler，就不中断逻辑
            if Context.get_value(utils.CONTEXT_KEY_PRTS_CURRENT_HANDLE) == '':
                return
            # 检查是否匹配到关键词
            _, texts, _ = value
            if self._check_keyword(['网络连接中断'], texts) \
                    or self._check_keyword(['数据已更新，即将进行同步'], texts)\
                    or self._check_keyword(['数据文件已过期，请重新登录'], texts)\
                    or self._check_keyword(['数据同步失败，请重新登录'], texts):
                # 有handler并且不是自己，中断掉它的逻辑走标准handle流程接管控制
                self.logger.info('intercept from ocr result, force finish current logic')
                raise utils.LogicFinishedException()

    @staticmethod
    def _check_keyword(keyword_list, texts):
        for word in keyword_list:
            if word not in texts:
                return False
        return True

    def can_handle(self) -> bool:
        return utils.roll_status(self, self.status_handler_map)

    def do_logic(self):
        utils.roll_status_and_checker(self, self.status_handler_map)

    @staticmethod
    def _status_data_updated_need_resynchronization() -> bool:
        return utils.check_keywords_from_context(['数据已更新，即将进行同步'])

    @staticmethod
    def _handle_data_updated_need_resynchronization():
        # 点击确认
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 805, 704, 1136, 775
        )
        utils.sleep(random.uniform(3, 5))
        raise utils.LogicFinishedException()

    @staticmethod
    def _status_login_expired() -> bool:
        return utils.check_keywords_from_context(['登录认证已失效，请重新登录'])

    @staticmethod
    def _handle_login_expired():
        # 点击确认
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 812, 710, 1123, 776
        )
        utils.sleep(random.uniform(5, 15))
        raise utils.LogicFinishedException()

    @staticmethod
    def _status_data_sync_failed() -> bool:
        return utils.check_keywords_from_context(['数据同步失败，请重新登录'])

    @staticmethod
    def _handle_data_sync_failed():
        # 点击确认
        utils.click.click_from_context(
            ScreenResolution(1600, 900), 620, 589, 1035, 645
        )
        utils.sleep(random.uniform(5, 15))
        raise utils.LogicFinishedException()


    @staticmethod
    def _status_data_expired() -> bool:
        return utils.check_keywords_from_context(['数据文件已过期，请重新登录'])

    @staticmethod
    def _handle_data_expired():
        # 点击确认
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 812, 710, 1123, 776
        )
        utils.sleep(random.uniform(5, 15))
        raise utils.LogicFinishedException()

    @staticmethod
    def _status_connection_lost() -> bool:
        return utils.check_keywords_from_context(['与神经网络连接丢失，请重新连接'])

    @staticmethod
    def _handle_connection_lost():
        # 点击确认
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 812, 710, 1123, 776
        )
        utils.sleep(random.uniform(5, 15))
        raise utils.LogicFinishedException()