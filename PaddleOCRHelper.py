import logging
import os
import sys

import cv2 as cv
import numpy as np
from paddleocr import PaddleOCR, paddleocr

from utils.controller.ADBController import ADBController

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
paddleocr.logging.disable(logging.DEBUG)

# 设置写入 DEBUG 级 log 到文件
logging.basicConfig(level=logging.INFO,
                    format=' %(asctime)s %(levelname)s: %(module)s: %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S %p',
                    stream=sys.stdout
                    )

logging.info("start initializing")

ocr = PaddleOCR(use_angle_cls=False, lang="ch")  # 初始化模型

logging.info("start read from adb")
# 获取图片
controller = ADBController()

while True:
    image = np.frombuffer(controller.get_device_screen_picture(), dtype="int8")
    # cv_image = cv.cvtColor(cv.imdecode(image, cv.IMREAD_COLOR), cv.COLOR_BGRA2RGB)
    cv_image = cv.imdecode(image, cv.IMREAD_COLOR)

    logging.info("start ocr")
    # 开始识别
    result = ocr.ocr(img=cv_image, cls=False)

    logging.info("process ocr result")

    logging.info(cv_image.shape)
    # cv_image = cv.imdecode(image, cv.IMREAD_COLOR)
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    # im_show = draw_ocr(image, boxes, txts, scores, font_path='./fonts/simfang.ttf')
    for index, box in enumerate(boxes):
        logging.info(f"{txts[index]}: {box[0][0]}, {box[0][1]}, {box[2][0]}, {box[2][1]}")
        cv.rectangle(
            img=cv_image, pt1=(int(box[0][0]), int(box[0][1])),
            pt2=(int(box[2][0]), int(box[2][1])),
            color=(255, 0, 0), thickness=3
        )
    cv.namedWindow('image_original', cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
    cv.imshow('image_original', cv_image)
    cv.waitKey(0)
