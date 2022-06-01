import logging
import random
import time

import utils
import utils.controller
from context import Context
from utils.click.ScrennClick import ClickZone, ScreenResolution
from utils.ocr.PaddleOCRProvider import request_ocr_result

logger = logging.getLogger('AutoBattleHandler')


class AutoBattleHandler:

    def __init__(self):
        self.auto_battle = ArknightsAutoBattle(
            allow_use_medicine=False
        )
        self.last_trigger_time = time.time() - 135 * 5 * 60 - 100  # 用于记录上一次触发的时间

    def can_handle(self) -> bool:
        # 如果上次触发时间到现在体力不满足一半，则暂时不触发
        if time.time() - self.last_trigger_time < 65 * 5 * 60:
            return False
        return self.auto_battle.try_detect_scene()
        # boxes, texts, scores = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        # if '仓库' in texts and '任务' in texts and '采购中心' in texts:
        #     return True
        # else:
        #     return False

    def do_logic(self):
        self.auto_battle.auto_fight()
        self.last_trigger_time = time.time()  # 更新上次触发时间


def _handle_terminal():
    """
    终端界面， 进入上一次战斗位置
    """

    utils.click.click_from_context('前往上一次作战')
    utils.sleep(random.uniform(3, 5))  # 等待游戏响应

    return True


class ArknightsAutoBattle:
    """ 不需要次数定时，一直刷，体力药保留开关 """

    class SanityUsedUpException(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class LogicFinishedException(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    def __init__(self, allow_use_medicine=False):
        """
        :param allow_use_medicine:  是否允许使用回体力药剂
        """
        self.logger = logging.getLogger('ArknightsAutoFighter')
        # 连接并初始化设备
        self.controller = Context.get_value(utils.controller.CONTEXT_KEY_CONTROLLER)
        self.click_helper = Context.get_value(utils.click.CONTEXT_KEY_CLICK_HELPER)
        # 初始化统计变量
        self.fight_finished = False
        self.fight_count = 1
        self.allow_use_medicine = bool(allow_use_medicine)

        # 扫描当前类里的所有函数，保留'_'开头的内部函数，以_handler_开头的函数作为状态处理函数
        self.status_handler_map = {}
        # 先检索_status_，产生key，然后检查handler函数
        for function_name in filter(lambda field: field.startswith('_status_'), dir(self)):
            actual_status_name = function_name[len('_status_'):]
            if hasattr(self, '_handle_' + actual_status_name):
                self.status_handler_map[(getattr(self, function_name))] = getattr(self,
                                                                                  '_handle_' + actual_status_name)
            else:
                self.status_handler_map[(getattr(self, function_name))] = self._default_status_handler
        self.logger.info(f"total read {len(self.status_handler_map)} handler")

    def _default_status_handler(self):
        pass

    def try_detect_scene(self) -> bool:
        for status_checker in self.status_handler_map:
            if status_checker():
                self.logger.info(f"detect status {status_checker.__name__[len('_status_'):]}")
                return True
        return False

    def auto_fight(self):
        # 循环调用auto_fight_once 来进行战斗
        # 退出情况有以下几种
        #   - 理智耗尽退出（正常退出）
        #   - 无法识别状态退出（异常退出）
        try:
            self._auto_fight()
        except ArknightsAutoBattle.SanityUsedUpException:
            self.logger.info(f'sanity used up, run exit progress')
            self._return_to_main_screen()
        except ArknightsAutoBattle.LogicFinishedException:
            self.logger.info(f'sanity used up, run exit progress')
            self._return_to_main_screen()
        except utils.StatusUnrecognizedException as status_unrecognized_exception:
            self.logger.exception(status_unrecognized_exception)
            raise status_unrecognized_exception
            # return False, status_unrecognized_exception

    def _auto_fight(self):
        """逻辑循环入口，通过Exception终结逻辑"""
        # 调用status_checker确定当前状态，然后根据状态执行动作，不再为每个关卡指定时间定时
        count_unknown_status = 0
        while True:
            request_ocr_result()  # 请求OCR
            # 根据配置列表，挨个key调用函数，返回True则调用value对应的列表
            # 没有状态匹配时对应Unknown状态，触发两次等待，如果还是不行就抛异常
            flag_status_checked = False
            for status_checker, status_handler in self.status_handler_map.items():
                if status_checker():
                    self.logger.info(f"start handler {status_handler.__name__[len('_handler_'):]}")
                    status_handler()
                    flag_status_checked = True
                    count_unknown_status = 0  # 重置未知状态计数
            if not flag_status_checked:
                # 未匹配上状态，等待两次，间隔10秒
                self.logger.info(f'no match status found ,waiting...')
                if count_unknown_status <= 2:
                    count_unknown_status += 1
                    utils.sleep(10)
                else:
                    # 超过2次，走异常脱离
                    raise utils.StatusUnrecognizedException()

    def _return_to_main_screen(self):

        self.logger.info(f"return to main screen")
        # 循环尝试点击主页按钮，然后检查OCR结果，如果没有识别到点击后应该出现的菜单，那就再点几次
        retry_count = 0
        while retry_count < 4:
            retry_count += 1

            point_x, point_y = self.click_helper.generate_target_click(ClickZone(
                ScreenResolution(1920, 1080), 296, 31, 524, 85
            ))
            self.controller.click(point_x, point_y)
            utils.sleep(random.uniform(3, 9))
            request_ocr_result()
            boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
            if '终端' in texts and '基建' in texts and '干员' in texts and '首页' in texts and '档案' in texts:
                # 任务完成跳出
                break
        if retry_count >= 4:
            raise utils.StatusUnrecognizedException()
        utils.click.click_from_context('首页')
        utils.sleep(random.uniform(6, 10))  # 等待游戏响应

    @staticmethod
    def _status_main_screen() -> bool:
        # 检查状态是否正确
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '终端' not in texts or '仓库' not in texts or '任务' not in texts or '采购中心' not in texts:
            return False
        return True

    @staticmethod
    def _handle_main_screen():
        """
        主界面，进入终端
        """
        utils.click.click_from_context('终端')
        utils.sleep(random.uniform(1, 5))  # 等待游戏响应

    @staticmethod
    def _status_terminal() -> bool:
        # 检查状态
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '前往上一次作战' not in texts or '终端' not in texts:
            return False
        return True

    @staticmethod
    def _status_level_selection() -> bool:
        # 检查状态是否正确
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '开始行动' not in texts or '代理指挥' not in texts:
            return False
        return True

    @staticmethod
    def _handle_level_selection():
        """
        关卡选择界面, 进入队伍选择界面
        """
        utils.click.click_from_context('开始行动')
        utils.sleep(random.uniform(5, 9))  # 等待游戏响应

    @staticmethod
    def _status_team_assemble() -> bool:
        # 检查状态是否正确
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '开始' not in texts or '行动' not in texts or '快捷编队' not in texts:
            return False
        return True

    @staticmethod
    def _handle_team_assemble():
        """
        队伍选择界面， 进入游戏界面
        """

        utils.click.click_from_context('开始')
        utils.sleep(random.uniform(5, 9))  # 等待游戏响应

    @staticmethod
    def _status_battle() -> bool:
        # 检查状态是否正确
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '接管作战' not in texts:
            return False
        return True

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
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '行动结束' not in texts:
            return False
        return True

    def _handle_level_settlement(self):
        """
        结算界面， 离开结算界面
        """

        # 执行逻辑
        self.fight_count += 1
        utils.click.click_from_context('行动结束')
        utils.sleep(random.uniform(5, 9))  # 等待游戏响应

    @staticmethod
    def _status_sanity_restore_medicine() -> bool:
        # 检查状态是否正确
        _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        if '使用药剂恢复' not in texts:
            return False
        return True

    def _handle_sanity_restore_medicine(self):
        """
        选择是否使用药剂的界面，确认使用恢复药剂
        """

        # 执行逻辑
        if not self.allow_use_medicine:
            # 关卡结算，通过逻辑结束异常跳出
            raise self.LogicFinishedException()

        self.logger.info('using medicine to restore sanity as intend')

        point_x, point_y = self.click_helper.generate_target_click(ClickZone(
            ScreenResolution(1920, 980), 1509, 745, 1609, 805
        ))

        self.controller.click(point_x, point_y)

        utils.sleep(random.uniform(3, 4))  # 等待游戏响应
