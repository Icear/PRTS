import logging

import cv2 as cv
import numpy
from paddleocr import PaddleOCR

from context import Context
from utils.OCR import CONTEXT_KEY_OCR_RESULT
from utils.controller import CONTEXT_KEY_CONTROLLER

ocr = PaddleOCR(use_angle_cls=False, lang="ch")  # 初始化模型
logger = logging.getLogger('PaddleOCR')


def request_ocr_result():
    """请求刷新OCR结果，结果保存至Context中，key为CONTEXT_KEY_OCR_RESULT"""
    data = Context.get_value(CONTEXT_KEY_CONTROLLER).get_device_screen_picture()
    image = numpy.frombuffer(data, dtype="int8")
    cv_image = cv.imdecode(image, cv.IMREAD_COLOR)
    logger.info("start ocr")
    result = ocr.ocr(img=cv_image, cls=False)
    logger.info("save ocr result to context")
    Context.set_value(CONTEXT_KEY_OCR_RESULT, result)
