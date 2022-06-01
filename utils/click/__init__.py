import utils
import utils.controller
import utils.ocr
from context import Context

CONTEXT_KEY_CLICK_HELPER = 'context_key_click_helper'


def click_from_context(text: str):
    """
    点击目标文字位置的方块
    :param text: 目标文字
    """
    boxes, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
    click_helper = Context.get_value(CONTEXT_KEY_CLICK_HELPER)
    controller = Context.get_value(utils.controller)

    index = texts.index(text)
    point_x, point_y = click_helper.generate_target_click(
        click_helper.current_screen_resolution.create_click_zone(
            boxes[index][0][0], boxes[index][0][1], boxes[index][2][0], boxes[index][2][1]
        )
    )
    controller.click(point_x, point_y)  # 点击时加上随机偏移量
