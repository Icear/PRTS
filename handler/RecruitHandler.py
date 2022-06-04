import json
import logging
import os.path
import random
import time
from functools import reduce

import utils.click
import utils.controller
import utils.ocr
from context import Context
from utils.click.ScrennClick import ScreenResolution


class RecruitHandler:

    def __init__(self):
        self.logger = logging.getLogger('ArknightsAutoFighter')

        self.status_handler_map = utils.generate_status_handler_map(self)

        # 初始化hr.json，生成tag_list
        with open(os.path.join(os.getcwd(), "hr.json"), 'r', encoding='utf-8') as hr_file:
            self.hr_list = json.load(hr_file)
            list(map(lambda operator: operator['tags'].append(operator['type'] + '干员'), self.hr_list))
            self.tag_list = set(reduce(
                lambda x, y: x.extend(y) or x,
                map(lambda operator: operator['tags'], self.hr_list)
            ))

        # 记录招募槽位情况
        self.slots_location = [
            ScreenResolution(1920, 1080).create_click_zone(28, 273, 948, 647),
            ScreenResolution(1920, 1080).create_click_zone(973, 272, 1895, 644),
            ScreenResolution(1920, 1080).create_click_zone(24, 688, 948, 1064),
            ScreenResolution(1920, 1080).create_click_zone(973, 690, 1895, 1058)
        ]
        # 记录招募槽位是否可操作
        self.slots_touchable = [
            True,
            True,
            True,
            True
        ]
        # 记录当前操作的槽位
        self.current_slot = -1

        # 用于记录上一次触发的时间
        self.last_trigger_time = time.time() - 135 * 5 * 60 - 100

    def can_handle(self) -> bool:
        # 如果上次触发时间到现在不满9个小时，则暂时不触发
        if time.time() - self.last_trigger_time < 9 * 60 * 60:
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
        主界面，进入公开招募
        """
        utils.click.click_text_from_context('公开招募')
        utils.sleep(random.uniform(3, 5))  # 等待游戏响应

        # 刷新slot状态
        self.slots_touchable = [
            True,
            True,
            True,
            True
        ]

    @staticmethod
    def _status_recruit_finished() -> bool:
        """
        公招界面，有已经完成的招募
        :return:
        """
        # 检查状态是否正确
        return utils.check_keywords_from_context(['公开招募', '已找到符合部分要求的候选人', '聘用候选人'])

    @staticmethod
    def _handle_recruit_finished():
        utils.click.click_text_from_context('聘用候选人')
        utils.sleep(random.uniform(5, 10))  # 等待游戏响应

    @staticmethod
    def _status_recruit_operator_package() -> bool:
        """
        招募结果界面，只有包没有干员的状态
        :return:
        """
        # 检查状态是否正确
        return utils.check_keywords_from_context(['SKIP'])

    @staticmethod
    def _handle_recruit_operator_package():

        utils.click.click_text_from_context('SKIP')
        utils.sleep(random.uniform(2, 4))  # 等待游戏响应

    @staticmethod
    def _status_recruit_operator_show() -> bool:
        """
        招募结果界面，干员出现的画面
        :return:
        """
        # 检查状态是否正确
        return utils.check_keywords_from_context(['资质凭证'])

    @staticmethod
    def _handle_recruit_operator_show():
        # 随便点击一个位置就好
        utils.click.click_text_from_context('资质凭证')
        utils.sleep(random.uniform(2, 4))  # 等待游戏响应

    @staticmethod
    def _status_start_recruit() -> bool:
        """
        主画面，有空闲操作可以选择开始招募干员
        :return:
        """
        # 检查状态是否正确
        return utils.check_keywords_from_context(['开始招募干员'])

    def _handle_start_recruit(self):
        # 读取槽位位置，记录数据
        boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
        for index, text in enumerate(texts):
            if '开始招募干员' == text:
                # 找到位置，检查slot对应
                slot_index = self._get_slot_index(boxes[index][0][0], boxes[index][0][1], boxes[index][2][0],
                                                  boxes[index][2][1])
                if not self.slots_touchable[slot_index]:
                    # 不能动的槽位
                    continue
                # 可以选取的
                self.current_slot = slot_index
                utils.click.click_text_from_context('开始招募干员')
                utils.sleep(random.uniform(2, 4))  # 等待游戏响应
                return
        # 全部都不能点，返回主界面
        self._handle_nothing_to_do()

    @staticmethod
    def _status_choose_operator_tag() -> bool:
        """
        干员招募。选择干员的位置
        :return:
        """
        # 检查状态是否正确
        return utils.check_keywords_from_context(['招募时限', '招募说明', '职业需求', '招募预算'])

    def _handle_choose_operator_tag(self):
        boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)

        # 从识别到的文字中筛选出公招标签
        available_tag_list = list(filter(lambda text: text in self.tag_list, texts))
        self.logger.info(f"read tags: {available_tag_list}")
        # 根据有效的公招标签，检查是否有组合能够筛选出四星以上的干员，有就侧重点击，否则空tag结束
        combo, result_level = self._compute_best_tags(available_tag_list)
        self.logger.info(f"read best combo: {combo}, expect to get {result_level} star operator")

        # 处理高资情况
        if result_level >= 6 or '资深干员' in combo or '资深干员' == combo:
            # 跳过这个槽位
            self.slots_touchable[self.current_slot] = False
            # 点击返回
            utils.click.click_from_context(
                ScreenResolution(1920, 1080), 1392, 952, 1527, 990
            )
            utils.sleep(random.uniform(2, 5))
            return

        # 处理低星但可刷新的情况
        if 3 >= result_level >= 2 and '点击刷新标签' in texts:
            self.logger.info(f"tag refresh available, try refresh")
            # 尝试刷新标签
            # 点击标签
            utils.click.click_from_context(
                ScreenResolution(1920, 1080), 1436, 583, 1475, 626
            )
            utils.sleep(random.uniform(0.7, 2))
            return

        # 点TAG
        if isinstance(combo, str):
            # 单个TAG的情况
            utils.click.click_text_from_context(combo)
        else:
            for tag in combo:
                utils.click.click_text_from_context(tag)
        # 点时间
        if result_level == 1:
            # 点1小时30分
            for _ in range(3):
                utils.click.click_from_context(
                    ScreenResolution(1920, 1080), 856, 206, 984, 238
                )
                utils.sleep(random.uniform(0.7, 2))

        else:
            # 点9小时
            utils.click.click_from_context(
                ScreenResolution(1920, 1080), 604, 428, 731, 460
            )
            utils.sleep(random.uniform(0.7, 2))
        # 点确定
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 1400, 853, 1523, 894
        )
        utils.sleep(random.uniform(2, 3))

    @staticmethod
    def _status_refresh_tag() -> bool:
        return utils.check_keywords_from_context(['是否消耗1次联络机会？'])

    @staticmethod
    def _handle_refresh_tag():
        # 确定
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 1061, 705, 1439, 776
        )
        utils.sleep(random.uniform(5, 7))

    @staticmethod
    def _status_nothing_to_do() -> bool:
        return utils.check_keywords_from_context(
            ['公开招募', '停止招募', '立即招募']) and utils.check_keywords_not_exists_from_context(['开始招募干员', '聘用候选人'])

    def _handle_nothing_to_do(self):
        # 回到主页面
        utils.click.click_from_context(
            ScreenResolution(1920, 1080), 45, 31, 176, 80
        )
        utils.sleep(random.uniform(4, 9))

        # 刷新上次操作时间
        self.last_trigger_time = time.time()
        raise utils.LogicFinishedException()

    def _compute_best_tags(self, available_tag_list: list) -> (list, int):
        """
        根据已有的TAG计算最合适的的TAG组合
        :param available_tag_list: 已有的TAG
        :return: 最佳TAG组合与对应星级
        """

        if '高级资深干员' in available_tag_list:
            return '高级资深干员', 6

        # TODO 优化下这里的计算，现在太晚了脑子里全是浆糊
        # 计算每种组合的最小星级数
        # 组合是从1、2、3三种选取方式里获得，生成map的tag
        result_map = {}
        # 1个
        for tag1 in available_tag_list:
            result_map[tag1] = -1
        # 2个
        for i in range(len(available_tag_list)):
            for j in range(i + 1, len(available_tag_list)):
                result_map[(available_tag_list[i], available_tag_list[j])] = -1
        # 3个
        for i in range(len(available_tag_list)):
            for j in range(i + 1, len(available_tag_list)):
                for k in range(j + 1, len(available_tag_list)):
                    result_map[(available_tag_list[i], available_tag_list[j], available_tag_list[k])] = -1

        # 根据每种key组合去检查是否有匹配的干员，并输出最小值，只查看超过2星的部分
        for combo in result_map.keys():
            # 扫描所有干员，检查匹配的干员，并且把期望中最小星级数记录到result_map里
            for operator in self.hr_list:
                # 跳过1星干员，避免干扰
                if operator['level'] < 2:
                    continue
                # 处理一个tag被识别成str的问题
                if isinstance(combo, str):
                    if combo not in operator['tags']:
                        continue
                else:
                    if not set(combo).issubset(operator['tags']):
                        continue
                # 当前TAG组合能够选择到这个干员
                if result_map[combo] != -1:
                    result_map[combo] = min(result_map[combo], operator['level'])  # 保存最小值
                else:
                    result_map[combo] = operator['level']  # 覆盖当前值

        # 扫描完成，读取现在的最大可获得星级
        best_combo = []
        current_best_result = 0
        for combo, best_result in result_map.items():
            if best_result > current_best_result:
                current_best_result = best_result
                best_combo = combo
        # 获得了最大的combo
        if current_best_result <= 4:
            # 看看有没有1星无敌TAG，4星可以放弃掉用来换1星
            if '支援机械' in available_tag_list:
                # 返回1星结果
                return '支援机械', 1
        # 没有触发特殊条件，那直接返回当前的最好选择
        return best_combo, current_best_result

    def _get_slot_index(self, left_up_x: int, left_up_y: int, right_bottom_x: int, right_bottom_y: int) -> int:
        """根据传入的矩形查找其所属的区域"""
        click_helper = Context.get_value(utils.click.CONTEXT_KEY_CLICK_HELPER)
        target_click_zone = click_helper.current_screen_resolution.create_click_zone(
            left_up_x, left_up_y, right_bottom_x, right_bottom_y
        )
        for index, zone in enumerate(self.slots_location):
            if zone.contains(target_click_zone):
                return index
        raise IndexError("unknown recruit slot index")
