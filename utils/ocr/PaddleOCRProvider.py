import logging

import cv2 as cv
import numpy
from paddleocr import PaddleOCR

import utils.controller
import utils.ocr
from context import Context

ocr = PaddleOCR(use_angle_cls=False, lang="ch")  # 初始化模型
logger = logging.getLogger('PaddleOCR')


def request_ocr_result():
    """请求刷新OCR结果，结果保存至Context中，key为CONTEXT_KEY_OCR_RESULT"""
    data = Context.get_value(utils.controller.CONTEXT_KEY_CONTROLLER).get_device_screen_picture()
    image = numpy.frombuffer(data, dtype="int8")
    cv_image = cv.imdecode(image, cv.IMREAD_COLOR)
    logger.info("start ocr")
    result = ocr.ocr(img=cv_image, cls=False)
    logger.info("save ocr result to context")
    Context.set_value(utils.ocr.CONTEXT_KEY_OCR_RESULT, result)
