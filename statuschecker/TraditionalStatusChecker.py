import logging
import os
import re

import cv2 as cv
import numpy as np


# 目的是根据当前屏幕的截图分辨出当前正在进行的状态
# 一共可能有的状态有：
#   - 关卡选择界面 level_selection
#       - 恢复体力界面-药剂恢复 restore_sanity_medicine
#       - 恢复体力界面-源石恢复 restore_sanity_stone
#   - 队伍选择界面 team_up
#   - 战斗界面 fighting
#   - 战斗结算界面 battle_settlement
#       - 剿灭结果汇报界面 annihilation_settlement
#       - 等级提升界面 level_up
# 截取每个界面的特征图片，初步实现是在1920，980分辨率下在同位置图片然后比对截取的图片是否相同；
# 之后的想法是用相同的模板图片来寻找截图中对应的位置，如果存在则有


class TraditionalStatusChecker:
    _template_path = os.path.join(os.getcwd(), 'template')
    ASC_STATUS_LEVEL_SELECTION = 'level_selection'
    ASC_STATUS_RESTORE_SANITY_MEDICINE = 'restore_sanity_medicine'
    ASC_STATUS_RESTORE_SANITY_STONE = 'restore_sanity_stone'
    ASC_STATUS_TEAM_UP = 'team_up'
    ASC_STATUS_FIGHTING = 'fighting'
    ASC_STATUS_BATTLE_SETTLEMENT = 'battle_settlement'
    ASC_STATUS_ANNIHILATION_SETTLEMENT = 'annihilation_settlement'
    ASC_STATUS_LEVEL_UP = 'level_up'
    ASC_STATUS_CONNECT_FAILED = 'connect_failed'
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

        # 配置 log
        self.logger = logging.getLogger('ArknightsStatusCheckHelper')

        #
        # 从template文件夹读取现有模板以及相关参数
        #
        # 根据状态列表生成模板字段
        self.templates = dict()
        status_list = list(filter(lambda name: (name.startswith("ASC_STATUS_") and name != 'ASC_STATUS_UNKNOWN'),
                                  dir(self)))
        self._status = list(map(lambda name: getattr(self, name), status_list))

        self.logger.info(f"loaded {len(self._status)} status")
        for status in self._status:
            self.templates[status] = list()

        template_files = os.listdir(self._template_path)
        self.logger.debug(f'list {len(template_files)} templates')

        # 为每个模板寻找其匹配的模板字典字段，并存入对应列表
        for template_file in template_files:
            for status in self._status:
                if template_file.startswith(status):
                    # 找到了对应坐标
                    template_data = self.read_template_data(template_file)
                    self.logger.debug(f"read template for {status}: {template_data.to_string()}")
                    self.templates[status].append(template_data)
                    self.logger.debug(f"load template {template_file} for {status} ")
                    break

        # 生成读取日志
        for status in self._status:
            self.logger.info(f"initialized {len(self.templates[status])} template for {status}")

    @staticmethod
    def read_template_data(template_file):
        reg_result = re.match(
            r'.*?-(\d*?)-(\d*?)-(\d*?)-(\d*?)\.png', template_file)
        template_data = \
            TraditionalStatusChecker.TemplateData(reg_result.group(1), reg_result.group(2),
                                                  reg_result.group(3), reg_result.group(4),
                                                  cv.imread(os.path.join(TraditionalStatusChecker._template_path,
                                                                         template_file), cv.IMREAD_GRAYSCALE)
                                                  )
        return template_data

    # 通过传入的屏幕截图来确定当前游戏状态
    def check_status(self, screen_shot):
        # 将读入的图片数据转为灰阶openCV用格式
        image = cv.imdecode(np.frombuffer(
            screen_shot, dtype="int8"), cv.IMREAD_GRAYSCALE)
        # 将图片传入每一个状态的匹配函数进行检查，获得匹配结果时返回该状态
        for status in self._status:
            if self._check_template(image, status):
                self.logger.info(f"checked status: {status}")
                return status
            # # 检查对应状态方法是否存在
            # if hasattr(self, f"check_{status}_status"):
            #     detector = getattr(self, f"check_{status}_status", lambda x: False)
            #     if detector(image):
            #         self.logger.info(f"checked status: {status}")
            #         return status  # 匹配成功
            # else:
            #     self.logger.warning(f"Status checker for status {status} not found! This status can not be detected.")
        self.logger.info(f"checked status: {self.ASC_STATUS_UNKNOWN}")
        return self.ASC_STATUS_UNKNOWN

    def _check_template(self, target_image, target):
        """
        check if template match the target image
        :param target_image: target image
        :param target: target status wanted
        :return: if template match the target image
        """
        for template in self.templates[target]:
            # check if templates is oversize
            target_image_shape = target_image.shape
            if target_image_shape[0] < template.end_y or target_image_shape[1] < template.end_x:
                # oversize template, skip
                self.logger.debug(f"skipped template check due to oversize template shape: {template.to_string()}")
                continue
            cut_image = target_image[
                        template.start_y:template.end_y,
                        template.start_x:template.end_x]
            # Otsu 阈值
            _, cut_image_new = cv.threshold(cut_image, 170, 255,
                                            cv.THRESH_BINARY + cv.THRESH_OTSU)
            _, template_image_new = cv.threshold(template.template_data, 170, 255,
                                                 cv.THRESH_BINARY + cv.THRESH_OTSU)

            difference = cv.absdiff(cut_image_new, template_image_new)
            mean, _ = cv.meanStdDev(difference)
            result = mean[0][0] < 10
            self.logger.debug(f"{target} get mean of difference: {mean}")
            self.logger.debug(
                f"status check show {result} for {target} template {template.to_string()} ")
            if result:
                return True
        return False

