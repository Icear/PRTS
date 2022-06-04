"""
在无人值守的情况下完成定时任务和循环

handler:
    - can_handle() bool 是否要接管
    - do_logic() 执行逻辑，遇到未知的状态就抛出异常要求介入，异常被处理完成后doLogic会被重新调用

- 有很多模块可以细分，它们可能从同一个状态（界面 ）开始触发
- 模块运行的过程中可能会因为突发影响，需要其它模块介入，介入后会重置
- 它们都需要

"""
import argparse
import logging
import os
import sys
import time

import handler.AutoBattleHandler
import utils.controller
import utils.controller.ADBController
import utils.ocr.PaddleOCRProvider
from context import Context
from utils.click.ScrennClick import ScreenResolution

handler_list = []
object_list = []

standby_mode_duration = 60 * 10


def initialize_global_tools():
    """初始化全局工具"""
    # ADBController
    adb_controller = utils.controller.ADBController.ADBController()
    adb_controller.wait_for_device()
    Context.set_value(utils.controller.CONTEXT_KEY_CONTROLLER, adb_controller)

    # 获取设备分辨率
    x, y = adb_controller.get_device_resolution()
    Context.set_value(utils.click.CONTEXT_KEY_CLICK_HELPER, utils.click.ScrennClick.ClickHelper(ScreenResolution(x, y)))

    # 初始化handler状态
    Context.set_value(utils.CONTEXT_KEY_PRTS_CURRENT_HANDLE, '')

    # 保存全局变量
    Context.set_value(handler.AutoBattleHandler.CONTEXT_KEY_CONFIGURATION_AUTO_BATTLE_HANDLER_ALLOW_USE_MEDICINE,
                      args.medicine)


def initialize_handlers():
    """扫描所有handler，然后循环触发各个模块的逻辑"""
    global handler_list, object_list
    # 扫描handler的模块并导入
    handler = __import__('handler')
    submodule_names = list(map(lambda file: os.path.splitext(file)[0],
                               filter(lambda file: not file.startswith('_'), os.listdir('handler'))
                               ))
    list(map(
        lambda module: __import__('handler.' + module),
        submodule_names
    ))
    for submodule_name in submodule_names:
        # 获取对应的class，构造出对象使其初始化，对于handler模块加入handler list
        submodule = getattr(handler, submodule_name)
        class_list = list(filter(lambda field: not field.startswith('_') and field.endswith('Handler'), dir(submodule)))

        for class_name in class_list:
            class_type = getattr(submodule, class_name)
            tmp_object = class_type()
            # 放入object_list，维持对象存在，便于突发影响模块启动
            object_list.append(tmp_object)
            # 检查是否实现了handler对应的函数
            if 'do_logic' not in dir(class_type) or 'can_handle' not in dir(class_type):
                continue
            # 加入handler_list
            handler_list.append(tmp_object)


def start_rules():
    # TODO 调用一次OCR，并且调用每个模块进行处理
    # 不断轮询所有模块，当can_handle都返回false时开始进入待机模式
    global handler_list, object_list
    while True:
        flag_module_finished = True
        utils.ocr.PaddleOCRProvider.request_ocr_result()  # 请求刷新OCR结果
        for handler in handler_list:
            if not handler.can_handle():
                continue
            # 请求获取权限的则读取数据
            flag_module_finished = False
            logging.info(f"module {handler.__class__.__qualname__} takes control")
            Context.set_value(utils.CONTEXT_KEY_PRTS_CURRENT_HANDLE, handler)  # 刷新Context中Handler
            try:
                handler.do_logic()
            except utils.StatusUnrecognizedException:
                logging.info(f"module {handler.__class__.__qualname__} reports unrecognized status")
            Context.set_value(utils.CONTEXT_KEY_PRTS_CURRENT_HANDLE, '')
            utils.ocr.PaddleOCRProvider.request_ocr_result()  # 请求刷新OCR结果
            logging.info(f"module {handler.__class__.__qualname__} released control")
        if flag_module_finished:
            # 所有模块都放弃了处理，进入待机模式，10分钟重新触发一次
            logging.info(f"enter standby mode, waiting for next cycle, sleep {standby_mode_duration}s")
            time.sleep(standby_mode_duration)


def main():
    initialize_global_tools()
    initialize_handlers()
    start_rules()


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--medicine',
                    help='allow using medicine to restore sanity, default false / 允许使用体力药水来恢复体力，默认为否',
                    default=False, action='store_true')
args = parser.parse_args()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format=' %(asctime)s %(levelname)s: %(module)s: %(message)s',
                        datefmt='%Y/%m/%d %I:%M:%S %p',
                        stream=sys.stdout
                        )
    main()
