import logging
import time

__all__ = ['click', 'controller', 'ocr']

import utils.ocr
from context import Context


def sleep(fake_time):
    logging.debug(f"schedule sleep for {fake_time} seconds")
    logging.debug(f"start sleep: {time.ctime()}")
    # a = 1
    time.sleep(fake_time)
    logging.debug(f"end sleep: {time.ctime()}")


class StatusUnrecognizedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def check_keywords_from_context(keyword_list):
    _, texts, _ = Context.get_value(utils.ocr.CONTEXT_KEY_OCR_RESULT)
    for word in keyword_list:
        if word not in texts:
            return False
    return True
