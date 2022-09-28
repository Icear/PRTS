import logging
import random
import time

import utils
import utils.controller
from context import Context
from utils.click.ScrennClick import ScreenResolution
from utils.ocr.PaddleOCRProvider import request_ocr_result

logger = logging.getLogger('AutoBattleHandler')
CONTEXT_KEY_CONFIGURATION_AUTO_BATTLE_HANDLER_ALLOW_USE_MEDICINE = \
    'context_key_configuration_auto_battle_handler_allow_use_medicine'


class AutoBattleHandler:

    def __init__(self):
        self.auto_battle = ArknightsAutoBattle(
            allow_use_medicine=Context.get_value(CONTEXT_KEY_CONFIGURATION_AUTO_BATTLE_HANDLER_ALLOW_USE_MEDICINE, False)
        )
        self.last_trigger_time = time.time() - 135 * 5 * 60 - 100  # 用于记录上一次触发的时间

    def can_handle(self) -> bool:
        # 如果上次触发时间到现在体力不满足一半，则暂时不触发
        if time.time() - self.last_trigger_time < 65 * 5 * 60:
            return False
        return self.auto_battle.try_detect_scene()

    def do_logic(self):
        self.auto_battle.auto_fight()
        self.last_trigger_time = time.time()  # 更新上次触发时间


class ArknightsAutoBattle:
    """ 不需要次数定时，一直刷，体力药保留开关 """

    class SanityUsedUpException(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    def __init__(self, allow_use_medicine=False):
        """
        :param allow_use_medicine:  是否允许使用回体力药剂
        """
        self.logger = logging.getLogger('ArknightsAutoFighter')
        # 初始化统计变量
        self.fight_finished = False
        self.fight_count = 1
        self.allow_use_medicine = bool(allow_use_medicine)

        # 扫描当前类里的所有函数，保留'_'开头的内部函数，以_handler_开头的函数作为状态处理函数
        self.status_handler_map = utils.generate_status_handler_map(self)

    def try_detect_scene(self) -> bool:
        return utils.roll_status(self, self.status_handler_map)

    def auto_fight(self):
        # 循环调用auto_fight_once 来进行战斗
        # 退出情况有以下几种
        #   - 理智耗尽退出（正常退出）
        #   - 无法识别状态退出（异常退出）
        try:
            self._auto_fight()
            self.logger.info(f'sanity used up, run exit progress')
            self._return_to_main_screen()
        except utils.StatusUnrecognizedException as status_unrecognized_exception:
            self.logger.exception(status_unrecognized_exception)
            raise status_unrecognized_exception
            # return False, status_unrecognized_exception

    def _auto_fight(self):
        """逻辑循环入口，通过Exception终结逻辑"""
        utils.roll_status_and_checker(self, self.status_handler_map)

    def _return_to_main_screen(self):
        self.logger.info(f"return to main screen")
        # 循环尝试点击主页按钮，然后检查OCR结果，如果没有识别到点击后应该出现的菜单，那就再点几次
        retry_count = 0
        while retry_count < 4:
            retry_count += 1
            utils.click.click_from_context(
                ScreenResolution(1920, 1080), 296, 31, 524, 85
            )
            utils.sleep(random.uniform(3, 9))
            request_ocr_result()
            boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
            if '终端' in texts and '基建' in texts and '干员' in texts and '首页' in texts and '档案' in texts:
                # 任务完成跳出
                break
        if retry_count >= 4:
            raise utils.StatusUnrecognizedException()
        utils.click.click_text_from_context('首页')
        utils.sleep(random.uniform(6, 10))  # 等待游戏响应

    @staticmethod
    def _status_main_screen() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['终端', '仓库', '任务', '采购中心'])

    @staticmethod
    def _handle_main_screen():
        """
        主界面，进入终端
        """
        utils.click.click_text_from_context('终端')
        utils.sleep(random.uniform(1, 5))  # 等待游戏响应

    @staticmethod
    def _status_terminal() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['前往上一次作战', '终端'])

    @staticmethod
    def _handle_terminal():
        """
        终端界面， 进入上一次战斗位置
        """
        utils.click.click_text_from_context('前往上一次作战')
        utils.sleep(random.uniform(3, 5))  # 等待游戏响应

    @staticmethod
    def _status_level_selection() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['开始行动', '代理指挥'])

    @staticmethod
    def _handle_level_selection():
        """
        关卡选择界面, 进入队伍选择界面
        """
        utils.click.click_text_from_context('开始行动')
        utils.sleep(random.uniform(5, 9))  # 等待游戏响应

    @staticmethod
    def _status_team_assemble() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['开始', '行动', '快捷编队'])

    @staticmethod
    def _handle_team_assemble():
        """
        队伍选择界面， 进入游戏界面
        """

        utils.click.click_text_from_context('开始')
        utils.sleep(random.uniform(5, 9))  # 等待游戏响应

    @staticmethod
    def _status_battle() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['接管作战'])

    @staticmethod
    def _handle_battle():
        """
        战斗界面，等待
        """

        # 执行逻辑
        utils.sleep(random.uniform(30, 60))  # 等待游戏响应

    @staticmethod
    def _status_level_settlement() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['行动结束'])

    def _handle_level_settlement(self):
        """
        结算界面， 离开结算界面
        """

        # 执行逻辑
        self.fight_count += 1
        utils.click.click_text_from_context('行动结束')
        utils.sleep(random.uniform(5, 9))  # 等待游戏响应

    @staticmethod
    def _status_sanity_restore_medicine() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['使用药剂恢复']) and utils.check_keywords_not_exists_from_context(
            ['是否花费1至纯源石兑换135理智？', '+135', '至纯源石不足']) 

    def _handle_sanity_restore_medicine(self):
        """
        选择是否使用药剂的界面，确认使用恢复药剂
        """

        # 执行逻辑
        if not self.allow_use_medicine:
            # 关卡结算，通过逻辑结束异常跳出
            raise utils.LogicFinishedException()

        self.logger.info('using medicine to restore sanity as intend')

        utils.click.click_from_context(
            ScreenResolution(1920, 980), 1509, 745, 1609, 805
        )
        utils.sleep(random.uniform(3, 4))  # 等待游戏响应

    @staticmethod
    def _status_sanity_restore_stone() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(
            ['是否花费1至纯源石兑换135理智？', '+135'])

    @staticmethod
    def _handle_sanity_restore_stone():
        """
        选择是否使用源石的界面，取消并结束
        """

        # 执行逻辑
        utils.click.click_from_context(
            ScreenResolution(1600, 900), 890, 690, 1050, 753
        )
        utils.sleep(random.uniform(3, 4))  # 等待游戏响应
        raise utils.LogicFinishedException()
    @staticmethod
    def _status_sanity_restore_no_stone() -> bool:
        # 检查状态是否正确
        return  utils.check_keywords_from_context(['至纯源石不足'])


    @staticmethod
    def _handle_sanity_restore_no_stone():
        """
        选择是否使用源石的界面，取消并结束
        """

        # 执行逻辑
        utils.click.click_from_context(
            ScreenResolution(1600, 900), 100, 690, 300, 753
        )
        utils.sleep(random.uniform(3, 4))  # 等待游戏响应
        raise utils.LogicFinishedException()
