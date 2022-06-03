import logging
import time

__all__ = ['click', 'controller', 'ocr']

import utils.ocr
from context import Context
from utils.ocr.PaddleOCRProvider import request_ocr_result

logger = logging.getLogger('utils')
# TODO 日志名称不对
CONTEXT_KEY_PRTS_CURRENT_HANDLE = 'context_key_prts_current_handle'


class LogicFinishedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class StatusUnrecognizedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def sleep(fake_time):
    logging.debug(f"schedule sleep for {fake_time} seconds")
    logging.debug(f"start sleep: {time.ctime()}")
    # a = 1
    time.sleep(fake_time)
    logging.debug(f"end sleep: {time.ctime()}")


def check_keywords_from_context(keyword_list):
    """检查目标关键词是否存在于Context中"""
    _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
    for word in keyword_list:
        if word not in texts:
            return False
    return True


def roll_status_and_checker(handler, status_handler_map: dict):
    """遍历handler内的status与handle并调用"""
    # 调用status_checker确定当前状态，然后根据状态执行动作，不再为每个关卡指定时间定时
    count_unknown_status = 0
    try:
        while True:
            request_ocr_result()  # 请求OCR
            # 根据配置列表，挨个key调用函数，返回True则调用value对应的列表
            # 没有状态匹配时对应Unknown状态，触发两次等待，如果还是不行就抛异常
            flag_status_checked = False
            for status_checker, status_handler in status_handler_map.items():
                if status_checker():
                    logger.info(f"start {type(handler).__name__} handler {status_handler.__name__[len('_handle_'):]}")
                    status_handler()
                    flag_status_checked = True
                    count_unknown_status = 0  # 重置未知状态计数
            if not flag_status_checked:
                # 未匹配上状态，等待两次，间隔10秒
                logger.info(f'no match status found ,waiting...')
                if count_unknown_status <= 2:
                    count_unknown_status += 1
                    utils.sleep(10)
                else:
                    # 超过2次，走异常脱离
                    raise utils.StatusUnrecognizedException()
    except utils.LogicFinishedException:
        logger.debug(f'handler {type(handler).__name__} reports progress finished')


def roll_status(handler, status_handler_map: dict) -> bool:
    """遍历handler内的status以检查是否有匹配数据"""
    for status_checker in status_handler_map:
        if status_checker():
            logger.info(f"{type(handler).__name__} detects status {status_checker.__name__[len('_handle_'):]}")
            return True
    return False


def generate_status_handler_map(handler) -> dict:
    """根据handler扫描生成其status_handler_map"""
    # 扫描当前类里的所有函数，保留'_'开头的内部函数，以_handler_开头的函数作为状态处理函数
    status_handler_map = {}
    # 先检索_status_，产生key，然后检查handler函数
    for function_name in filter(lambda field: field.startswith('_status_'), dir(handler)):
        actual_status_name = function_name[len('_status_'):]
        if hasattr(handler, '_handle_' + actual_status_name):
            status_handler_map[(getattr(handler, function_name))] = getattr(handler,
                                                                            '_handle_' + actual_status_name)
        else:
            handler.status_handler_map[(getattr(handler, function_name))] = _default_status_handler
    logger.info(f"total read {len(status_handler_map)} status from handler {type(handler).__name__}")
    return status_handler_map


def _default_status_handler():
    pass
