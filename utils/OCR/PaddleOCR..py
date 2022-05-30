import logging

import cv2 as cv
import numpy
from paddleocr import PaddleOCR

from context import Context

CONTEXT_KEY_OCR_RESULT = 'context_key_ocr_result'

ocr = PaddleOCR(use_angle_cls=False, lang="ch")  # 初始化模型
logger = logging.getLogger('PaddleOCR')


def request_ocr_result(data: bytes):
    image = numpy.frombuffer(data, dtype="int8")
    cv_image = cv.imdecode(image, cv.IMREAD_COLOR)
    logger.info("start ocr")
    result = ocr.ocr(img=cv_image, cls=False)
    logging.info("save ocr result to context")
    Context.set_value(CONTEXT_KEY_OCR_RESULT, result)
