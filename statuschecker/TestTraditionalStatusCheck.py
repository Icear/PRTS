import logging
import os
import sys

from statuschecker import TraditionalStatusChecker

if __name__ == '__main__':

    # 设置写入 DEBUG 级 log 到控制台
    logging.basicConfig(level=logging.DEBUG,
                        format=' %(asctime)s %(levelname)s: %(module)s: %(message)s',
                        datefmt='%Y/%m/%d %I:%M:%S %p',
                        stream=sys.stdout
                        )

    # 把test_case下的所有图片读出来，丢给目标函数检查，输出每一次的检查结果和被检查的文件名

    target_images = {}
    status_checker = TraditionalStatusChecker.TraditionalStatusChecker()

    for test_file in os.listdir(os.path.join(os.getcwd(), 'test_case')):
        # image = cv.imread(
        #     os.path.join(os.getcwd(), 'test_case', test_file), cv.IMREAD_GRAYSCALE
        # )
        with open(os.path.join(os.getcwd(), 'test_case', test_file), 'rb+') as file:
            image = file.read()
        target_images[test_file] = image
    print(f"read {len(target_images)} test cases")

    success_count = 0
    fail_count = 0

    test_target = status_checker.ASC_STATUS_ANNIHILATION_SETTLEMENT
    test_active_only = False

    test_string = {
        status_checker.ASC_STATUS_LEVEL_SELECTION: "enter_team_up",
        status_checker.ASC_STATUS_TEAM_UP: "enter_game",
        status_checker.ASC_STATUS_BATTLE_SETTLEMENT: "leave_settlement",
        status_checker.ASC_STATUS_FIGHTING: "fighting",
        status_checker.ASC_STATUS_RESTORE_SANITY_MEDICINE: "restore_sanity_medicine",
        status_checker.ASC_STATUS_RESTORE_SANITY_STONE: "restore_sanity_stone",
        status_checker.ASC_STATUS_ANNIHILATION_SETTLEMENT: "annihilation_settlement",
        status_checker.ASC_STATUS_LEVEL_UP: "level_up"
    }

    for case_name, image in target_images.items():
        actual = test_string[test_target] in case_name
        # 当test_active_onely 为真时只测试正向case，为负时测全部
        if test_active_only and not actual:
            continue
        test_result = status_checker.check_status(image)
        if (test_result == test_target) == actual:
            success_count += 1
        else:
            fail_count += 1
            print(f"failed test case: {case_name}, wanted result is {actual}, but get {test_result}")
    print(f"test finished, success: {success_count}, fail: {fail_count}")
