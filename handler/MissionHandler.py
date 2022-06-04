import logging
import random
import time

import utils
from utils.click import ScreenResolution


class MissionHandler:
    def __init__(self):
        self.status_handler_map = utils.generate_status_handler_map(self)
        self.logger = logging.getLogger('MissionHandler')

        # 记录一下当前操作状态
        self.slot_finished = [False, False]
        self.current_work_slot = 1

        # 用于记录上一次触发的时间
        self.last_trigger_time = time.time() - 135 * 5 * 60 - 100

    def can_handle(self) -> bool:
        # 如果上次触发时间到现在不满5个小时，则暂时不触发
        if time.time() - self.last_trigger_time < 1 * 60 * 60:
            return False
        # 满足了条件
        return utils.roll_status(self, self.status_handler_map)

    def do_logic(self):
        utils.roll_status_and_checker(self, self.status_handler_map)

    @staticmethod
    def _status_main_screen() -> bool:
        # 检查状态是否正确
        return utils.check_keywords_from_context(['终端', '仓库', '任务', '采购中心'])

    def _handle_main_screen(self):
        """
        主界面，进入任务
        """
        utils.click.click_text_from_context('任务')
        utils.sleep(random.uniform(3, 5))  # 等待游戏响应
        # 重置状态
        self.slot_finished = [False, False]
        self.current_work_slot = 0

    @staticmethod
    def _status_mission():
        return utils.check_keywords_from_context(['周常任务']) or utils.check_keywords_from_context(['t24日常任务'])

    def _handle_mission(self):
        # 直接在这里把两个地方的任务都领取掉，因为没办法区分

        # 查看是否可以做个人任务
        if self.current_work_slot == 0 and not self.slot_finished[self.current_work_slot]:
            # 点击切换到个人任务上
            utils.click.click_text_from_context('t24日常任务')
            utils.sleep(random.uniform(1, 2))
            if utils.check_keywords_from_context(['收集全部']):
                # 开始点击
                utils.click.click_text_from_context('收集全部')
                utils.sleep(random.uniform(6, 10))
                return
            else:
                # 没得点，没有任务能做，更新标记，切换到2号位置
                self.slot_finished[self.current_work_slot] = True
                self.current_work_slot = 1
                return

        # 查看是否可以做周常任务
        if self.current_work_slot == 1 and not self.slot_finished[self.current_work_slot]:
            # 点击切换到周常任务上
            utils.click.click_text_from_context('周常任务')
            utils.sleep(random.uniform(1, 2))
            # 开始点击
            if utils.check_keywords_from_context(['收集全部']):
                utils.click.click_text_from_context('收集全部')
                utils.sleep(random.uniform(6, 10))
                return
            else:
                # 没得点，没有任务能做，更新标记
                self.slot_finished[self.current_work_slot] = True

        # 无事可做，结束，返回上一层
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 41, 32, 201, 80
        )
        utils.sleep(random.uniform(3, 5))
        self.last_trigger_time = time.time()
        raise utils.LogicFinishedException()

    @staticmethod
    def _status_receive_rewards() -> bool:
        return utils.check_keywords_from_context(['获得物资'])

    @staticmethod
    def _handle_receive_rewards():
        utils.click.click_text_from_context('获得物资')
