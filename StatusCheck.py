import cv2 as cv
import os
import numpy as np
#
# 关卡选择模板
#
template_image_level_selection = cv.imread(
    os.path.join(os.getcwd(), 'template', 'level_selection-1705-877-1853-917.png'))
target_image_level_selection = cv.imread(
    os.path.join(os.getcwd(), 'log1', 'log-2020-1-4-13-24-56-enter_company_interface(1648,906).png'))

cut_image_level_selection = target_image_level_selection[877:917, 1705:1853]

# 全局阈值
difference = cv.subtract(cut_image_level_selection, template_image_level_selection)
result = not np.any(difference)
print(result)
# cv.imshow('cut_image', cut_image_level_selection)
# cv.imshow('template_image', template_image_level_selection)
# cv.waitKey(0)

#
# 队伍选择模板
#
template_image_team_up = cv.imread(os.path.join(os.getcwd(), 'template', 'team_up-1523-640-1661-778.png'))
target_image_team_up = cv.imread(
    os.path.join(os.getcwd(), 'log1', 'log-2020-1-4-13-25-5-enter_game(1616,585).png'))
cut_image_team_up = target_image_team_up[640:778, 1523:1661]

# 全局阈值
difference = cv.subtract(cut_image_team_up, template_image_team_up)
result = not np.any(difference)
print(result)
# cv.imshow('cut_image', cut_image_team_up)
# cv.imshow('template_image', template_image_team_up)
# cv.waitKey(0)


#
# 游戏结算模板
#
# 模板图片
template_image_battle_settlement = cv.imread(
    os.path.join(os.getcwd(), 'template', 'battle_settlement-53-794-538-913.png'), cv.IMREAD_GRAYSCALE)
# 正向目标图片
target_image_battle_settlement = cv.imread(
    os.path.join(os.getcwd(), 'log1', 'log-2020-1-4-13-26-51-leave_summarize_interface(1544,592).png'),
    cv.IMREAD_GRAYSCALE)
cut_image_battle_settlement = target_image_battle_settlement[794:913, 53:538]
# 消极目标图片
negative_target_image_battle_settlement = cv.imread(
    os.path.join(os.getcwd(), 'log1', 'log-2020-1-4-13-27-11-enter_game(1589,574).png'),
    cv.IMREAD_GRAYSCALE)
cut_negative_target_image_battle_settlement = negative_target_image_battle_settlement[794:913, 53:538]
# Otsu 阈值
_, cut_image_battle_settlement_new = cv.threshold(cut_image_battle_settlement, 170, 255,
                                                  cv.THRESH_BINARY + cv.THRESH_OTSU)
_, template_image_battle_settlement_new = cv.threshold(template_image_battle_settlement, 170, 255,
                                                       cv.THRESH_BINARY + cv.THRESH_OTSU)
_, cut_negative_image_battle_settlement = cv.threshold(cut_negative_target_image_battle_settlement, 170, 255,
                                                  cv.THRESH_BINARY + cv.THRESH_OTSU)
#
# # 经过高斯滤波的 Otsu 阈值
#
# cut_image_battle_settlement_blur = cv.GaussianBlur(cut_image_battle_settlement, (5, 5), 0)
# template_image_battle_settlement_blur = cv.GaussianBlur(template_image_battle_settlement, (5, 5), 0)
# _, cut_image_battle_settlement_new = cv.threshold(cut_image_battle_settlement_blur, 0, 255,
#                                                   cv.THRESH_BINARY + cv.THRESH_OTSU)
# _, template_image_battle_settlement_new = cv.threshold(template_image_battle_settlement_blur, 0, 255,
#                                                        cv.THRESH_BINARY + cv.THRESH_OTSU)
difference = cv.subtract(cut_image_battle_settlement_new, template_image_battle_settlement_new)
# difference = cv.subtract(cut_negative_image_battle_settlement, template_image_battle_settlement_new)
mean, std_dev = cv.meanStdDev(difference)
# print(mean)
# print(std_dev)
result = mean[0][0] < 1
print(result)
# 同位置差异值：均值mean = 0.20324006，标准差std_dev = 7.19617318
# 异位置差异值：均值mean = 64.59499264, 标准差std_dev = 110.90180363
# result = not np.any(difference)
# print(result)
# cv.imshow('cut_image', cut_image_battle_settlement_new)
# cv.imshow('cut_negative_image', cut_negative_image_battle_settlement)
# cv.imshow('template_image', template_image_battle_settlement_new)
# cv.imshow('difference', difference)
# cv.waitKey(0)
#
# cv.destroyAllWindows()
image = cv.cvtColor(template_image_level_selection,cv.COLOR_BGR2GRAY)
cv.imshow('image',image)
cv.waitKey(0)
cv.destroyAllWindows()