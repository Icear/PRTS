import os
import cv2 as cv
import re
import logging
import numpy as np


# 目的是根据当前屏幕的截图分辨出当前正在进行的状态
# 一共可能有的状态有：
#   - 关卡选择界面 level_selection
#       - 体力不足界面 lose_mind
#   - 队伍选择界面 team_up
#   - 战斗界面 fighting
#   - 战斗结算界面 battle_settlement
#       - 剿灭结果汇报界面 annihilation_settlement
# 截取每个界面的特征图片，初步实现是在1920，960分辨率下在同位置图片然后比对截取的图片是否相同；
# 之后的想法是用相同的模板图片来寻找截图中对应的位置，如果存在则有


class ArknightsStatusChecker:
    logger = logging.getLogger('ArknightsStatusCheckHelper')
    _template_path = os.path.join(os.getcwd(), 'template')
    ASC_STATUS_LEVEL_SELECTION = 'level_selection'
    ASC_STATUS_LOSE_MIND = 'lose_mind'
    ASC_STATUS_TEAM_UP = 'temp_up'
    ASC_STATUS_FIGHTING = 'fighting'
    ASC_STATUS_BATTLE_SETTLEMENT = 'battle_settlement'
    ASC_STATUS_ANNIHILATION_SETTLEMENT = 'annihilation_settlement'
    ASC_STATUS_UNKNOWN = 'unknown'

    class TemplateData:
        def __init__(self, start_x, start_y, end_x, end_y, template_data):
            self.start_x = int(start_x)
            self.start_y = int(start_y)
            self.end_x = int(end_x)
            self.end_y = int(end_y)
            self.template_data = template_data

        def to_string(self):
            return f"start_x: {self.start_x}, start_y: {self.start_y}, end_x: {self.end_x}, end_y: {self.end_y}"

    def __init__(self):
        #
        # 从template文件夹读取现有模板以及相关参数
        #
        self.level_selection_templates = list()
        self.team_up_templates = list()
        self.battle_settlement_templates = list()

        template_files = os.listdir(self._template_path)
        self.logger.debug(f'list {len(template_files)} templates')

        for template_file in template_files:
            # 读取判断关卡选择界面模板
            if template_file.startswith(self.ASC_STATUS_LEVEL_SELECTION):
                template_data = self.read_template_data(template_file)
                self.logger.debug(f"read template for level selection: {template_data.to_string()}")
                self.level_selection_templates.append(template_data)
                continue
            # 读取判断队伍选择界面模板
            if template_file.startswith(self.ASC_STATUS_TEAM_UP):
                template_data = self.read_template_data(template_file)
                self.logger.debug(f"read template for team up: {template_data.to_string()}")
                self.team_up_templates.append(template_data)
                continue
            # 读取结算界面模板
            if template_file.startswith(self.ASC_STATUS_BATTLE_SETTLEMENT):
                template_data = self.read_template_data(template_file)
                self.logger.debug(f"read template for battle settlement: {template_data.to_string()}")
                self.battle_settlement_templates.append(template_data)
                continue
        self.logger.info(f"initialized {len(self.level_selection_templates)} template for level selection")
        self.logger.info(f"initialized {len(self.team_up_templates)} template for team up")
        self.logger.info(f"initialized {len(self.battle_settlement_templates)} template for battle settlement")

    @staticmethod
    def read_template_data(template_file):
        reg_result = re.match(
            r'.*?-(\d*?)-(\d*?)-(\d*?)-(\d*?)\.png', template_file)
        template_data = \
            ArknightsStatusChecker.TemplateData(reg_result.group(1), reg_result.group(2),
                                                reg_result.group(3), reg_result.group(4),
                                                cv.imread(os.path.join(ArknightsStatusChecker._template_path,
                                                                       template_file))
                                                )
        return template_data

    # 用于生成模板，读取目标图片并弹出窗口以供剪切模板，剪切后输出至当前目录
    @staticmethod
    def cut_template(filepath, target_status):
        image = cv.imread(filepath, cv.IMREAD_GRAYSCALE)
        # cv.IMREAD_UNCHANGED
        flags = True
        start_x = 0
        start_y = 0
        end_x = 0
        end_y = 0

        def cut(event, x, y, flag, param):
            global flags, start_x, start_y, end_x, end_y
            if event == cv.EVENT_LBUTTONDOWN:
                if flags:
                    start_x = x
                    start_y = y
                    flags = False
                else:
                    end_x = x
                    end_y = y

        cv.namedWindow('image_original', cv.WINDOW_NORMAL)
        cv.setMouseCallback('image_original', cut)
        cv.imshow('image_original', image)
        cv.waitKey(0)
        print(start_x)
        print(start_y)
        print(end_x)
        print(end_y)
        newimg = image[start_y:end_y, start_x:end_x]
        cv.imshow('image', newimg)
        cv.waitKey(0)
        cv.imwrite(os.path.join(os.getcwd(), f"{target_status}-{start_x}-{start_y}-{end_x}-{end_y}.png"), newimg)
        cv.destroyAllWindows()

    # 通过传入的屏幕截图来确定当前游戏状态
    def check_status(self, screen_shot):
        image = cv.imdecode(np.frombuffer(
            screen_shot, dtype="int8"), cv.IMREAD_UNCHANGED)
        if self.check_level_selection_status(image):
            return self.ASC_STATUS_LEVEL_SELECTION
        if self.check_team_up_status(image):
            return self.ASC_STATUS_TEAM_UP
        if self.check_battle_settlement(image):
            return self.ASC_STATUS_BATTLE_SETTLEMENT
        return self.ASC_STATUS_UNKNOWN

    def check_level_selection_status(self, target_image_level_selection):
        for level_selection_template in self.level_selection_templates:
            cut_image_level_selection = target_image_level_selection[
                                        level_selection_template.start_y:level_selection_template.end_y,
                                        level_selection_template.start_x:level_selection_template.end_x]

            # 全局阈值
            difference = cv.subtract(cut_image_level_selection, level_selection_template.template_data)
            result = not np.any(difference)
            self.logger.debug(
                f"status check show {result} for level selection template {level_selection_template.to_string()} ")
            if not result:
                return False
        return True

    def check_team_up_status(self, target_image_team_up):
        for team_up_template in self.team_up_templates:
            cut_image_team_up = target_image_team_up[
                                team_up_template.start_y:team_up_template.end_y,
                                team_up_template.start_x:team_up_template.end_x]

            # 全局阈值
            difference = cv.subtract(cut_image_team_up, team_up_template.template_data)
            result = not np.any(difference)
            self.logger.debug(
                f"status check show {result} for team up template {team_up_template.to_string()} ")
            if not result:
                return False
        return True

    def check_battle_settlement(self, target_image_battle_settlement):
        for battle_settlement_template in self.battle_settlement_templates:
            # 模板图片
            template_image_battle_settlement = cv.cvtColor(battle_settlement_template.template_data, cv.COLOR_BGR2GRAY)
            # 目标图片
            target_image_battle_settlement = cv.cvtColor(target_image_battle_settlement, cv.COLOR_BGR2GRAY)
            cut_image_battle_settlement = target_image_battle_settlement[794:913, 53:538]

            # Otsu 阈值
            _, cut_image_battle_settlement_new = cv.threshold(cut_image_battle_settlement, 170, 255,
                                                              cv.THRESH_BINARY + cv.THRESH_OTSU)
            _, template_image_battle_settlement_new = cv.threshold(template_image_battle_settlement, 170, 255,
                                                                   cv.THRESH_BINARY + cv.THRESH_OTSU)

            difference = cv.subtract(cut_image_battle_settlement_new, template_image_battle_settlement_new)
            mean, _ = cv.meanStdDev(difference)
            result = mean[0][0] < 1
            self.logger.debug(
                f"status check show {result} for team up template {battle_settlement_template.to_string()} ")
            if not result:
                return False
        return True


if __name__ == '__main__':
    status_checker = ArknightsStatusChecker()
    # status_checker.cut_template(
    #     os.path.join(os.getcwd(), 'log1', 'log-2020-1-4-13-24-43-leave_summarize_interface(1473,546).png'))
