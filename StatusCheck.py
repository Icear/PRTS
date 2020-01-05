import cv2 as cv
import os
import numpy as np


def test_level_selection(target_image_level_selection):
    #
    # 关卡选择模板
    #
    template_image = cv.imread(
        os.path.join(os.getcwd(), 'template', 'level_selection-1705-877-1853-917.png'), cv.IMREAD_GRAYSCALE)

    cut_image = target_image_level_selection[877:917, 1705:1853]

    # 全局阈值
    difference = cv.absdiff(cut_image, template_image)
    result = not np.any(difference)
    print(result)
    cv.imshow('cut_image', cut_image)
    cv.imshow('template_image', template_image)
    cv.imshow('difference', difference)
    cv.waitKey(0)
    return result


def test_team_up(target_image_team_up):
    #
    # 队伍选择模板
    #
    template_image = cv.imread(os.path.join(os.getcwd(), 'template', 'team_up-1523-640-1661-778.png'),
                               cv.IMREAD_GRAYSCALE)

    cut_image = target_image_team_up[640:778, 1523:1661]

    # 全局阈值
    difference = cv.absdiff(cut_image, template_image)
    result = not np.any(difference)
    print(result)
    cv.imshow('cut_image', cut_image)
    cv.imshow('template_image', template_image)
    cv.imshow('difference', difference)
    cv.waitKey(0)


def test_battle_settlement(target_image_battle_settlement):
    #
    # 游戏结算模板
    #
    # 模板图片
    template_image = cv.imread(
        os.path.join(os.getcwd(), 'template', 'battle_settlement-53-794-538-913.png'), cv.IMREAD_GRAYSCALE)

    # 正向目标图片
    cut_image = target_image_battle_settlement[794:913, 53:538]

    # Otsu 阈值
    _, cut_image_battle_settlement_new = cv.threshold(cut_image, 170, 255,
                                                      cv.THRESH_BINARY + cv.THRESH_OTSU)
    _, template_image_battle_settlement_new = cv.threshold(template_image, 170, 255,
                                                           cv.THRESH_BINARY + cv.THRESH_OTSU)

    difference = cv.absdiff(cut_image_battle_settlement_new, template_image_battle_settlement_new)
    mean, std_dev = cv.meanStdDev(difference)
    # print(mean)
    # print(std_dev)
    result = mean[0][0] < 1
    print(result)
    cv.imshow('cut_image', cut_image)
    cv.imshow('template_image', template_image)
    cv.imshow('difference', difference)
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == '__main__':
    target_image_level_selection = cv.imread(
        os.path.join(os.getcwd(), 'test_case', 'log-2020-1-4-13-24-56-enter_company_interface(1648,906).png'),
        cv.IMREAD_GRAYSCALE)
    target_image_team_up = cv.imread(
        os.path.join(os.getcwd(), 'test_case', 'log-2020-1-4-13-25-5-enter_game(1616,585).png'), cv.IMREAD_GRAYSCALE)
    target_image_battle_settlement = cv.imread(
        os.path.join(os.getcwd(), 'test_case', 'log-2020-1-4-13-26-51-leave_summarize_interface(1544,592).png'),
        cv.IMREAD_GRAYSCALE)
    target_image_fighting = cv.imread(
        os.path.join(os.getcwd(), 'test_case', 'MuMu20200105200255.png'),
        cv.IMREAD_GRAYSCALE)
    # test_level_selection(target_image_level_selection)
    # test_level_selection(target_image_team_up)
    # test_level_selection(target_image_battle_settlement)
    # test_level_selection(target_image_fighting)
    # test_team_up(target_image_level_selection)
    # test_team_up(target_image_team_up)
    # test_team_up(target_image_battle_settlement)
    # test_team_up(target_image_fighting)
    test_battle_settlement(target_image_level_selection)
    test_battle_settlement(target_image_team_up)
    test_battle_settlement(target_image_battle_settlement)
    test_battle_settlement(target_image_fighting)
