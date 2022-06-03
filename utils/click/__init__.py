import utils
import utils.controller
import utils.ocr
from context import Context
from utils.click.ScrennClick import ScreenResolution

CONTEXT_KEY_CLICK_HELPER = 'context_key_click_helper'


def click_text_from_context(text: str):
    """
    点击目标文字位置的方块
    :param text: 目标文字
    """
    boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
    click_helper = Context.get_value(CONTEXT_KEY_CLICK_HELPER)
    controller = Context.get_value(utils.controller.CONTEXT_KEY_CONTROLLER)
    index = texts.index(text)
    point_x, point_y = click_helper.generate_target_click(
        click_helper.current_screen_resolution.create_click_zone(
            boxes[index][0][0], boxes[index][0][1], boxes[index][2][0], boxes[index][2][1]
        )
    )
    controller.click(point_x, point_y)  # 点击时加上随机偏移量


def click_every_same_text_from_context(text: str):
    """
    点击所有包含目标文字方块的位置
    :param text: 目标文字
    """
    boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
    click_helper = Context.get_value(CONTEXT_KEY_CLICK_HELPER)
    controller = Context.get_value(utils.controller.CONTEXT_KEY_CONTROLLER)
    index = 0
    try:
        while True:
            index = texts.index(text, index)
            point_x, point_y = click_helper.generate_target_click(
                click_helper.current_screen_resolution.create_click_zone(
                    boxes[index][0][0], boxes[index][0][1], boxes[index][2][0], boxes[index][2][1]
                )
            )
            controller.click(point_x, point_y)  # 点击时加上随机偏移量
    except ValueError:
        pass


def click_from_context(screen_resolution: ScreenResolution, left_top_x: int, left_top_y: int, right_down_x: int,
                       right_down_y: int):
    """
    根据传入的点击配置进行点击
    :param screen_resolution: 传入可点击区域所对应的屏幕参数
    :param left_top_x: 可点击区域左上角坐标x
    :param left_top_y: 可点击区域左上角坐标y
    :param right_down_x: 可点击区域右下角坐标x
    :param right_down_y: 可点击区域右下角坐标y
    """
    click_helper = Context.get_value(CONTEXT_KEY_CLICK_HELPER)
    controller = Context.get_value(utils.controller.CONTEXT_KEY_CONTROLLER)

    point_x, point_y = click_helper.generate_target_click(
        screen_resolution.create_click_zone(left_top_x, left_top_y, right_down_x, right_down_y)
    )
    controller.click(point_x, point_y)
