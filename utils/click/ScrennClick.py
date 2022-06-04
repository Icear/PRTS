import random


class ScreenResolution:
    def __init__(self, length_x, width_y):
        self.length = int(length_x)
        self.width = int(width_y)
        if self.length < self.width:
            self.length, self.width = self.width, self.length

    def create_click_zone(self, left_up_x, left_up_y, right_down_x, right_down_y):
        return ClickZone(self, left_up_x, left_up_y, right_down_x, right_down_y)


class ClickZone:
    """保存可点击的区域，以及所属的屏幕尺寸"""

    def __init__(self, resolution: ScreenResolution, left_up_x: int, left_up_y: int, right_down_x: int,
                 right_down_y: int):
        self.resolution = resolution
        self.left_up_x = int(left_up_x)
        self.left_up_y = int(left_up_y)
        self.right_down_x = int(right_down_x)
        self.right_down_y = int(right_down_y)

    def contains(self, click_zone) -> bool:
        # 先缩放到相同分辨率
        click_zone.scale_to_target_resolution(self.resolution)
        # 检查是否存在包含关系，只检测完全包含
        if self.left_up_x <= click_zone.left_up_x \
                and self.left_up_y <= click_zone.left_up_y \
                and self.right_down_x >= click_zone.right_down_x \
                and self.right_down_y >= click_zone.right_down_y:
            return True

        return False

    def scale_to_target_resolution(self, target_resolution: ScreenResolution):
        """将当前ClickZone缩放到目标分辨率"""
        self.left_up_x = int(self.left_up_x / self.resolution.length * target_resolution.length)
        self.left_up_y = int(self.left_up_y / self.resolution.width * target_resolution.width)
        self.right_down_x = int(self.right_down_x / self.resolution.length * target_resolution.length)
        self.right_down_y = int(self.right_down_y / self.resolution.width * target_resolution.width)
        self.resolution = target_resolution


class ClickHelper:
    def __init__(self, current_screen_resolution: ScreenResolution):
        """记录当前的屏幕分辨率"""
        self.current_screen_resolution = current_screen_resolution

    def generate_target_click(self, click_zone: ClickZone) -> (int, int):
        """根据目标屏幕分辨率，计算并生成点击位置"""
        # 从原始区域里选取点
        point_x = random.uniform(click_zone.left_up_x, click_zone.right_down_x)
        point_y = random.uniform(click_zone.left_up_y, click_zone.right_down_y)

        # 将点转化为目标分辨率的点
        new_x = point_x / click_zone.resolution.length * self.current_screen_resolution.length
        new_y = point_y / click_zone.resolution.width * self.current_screen_resolution.width
        return new_x, new_y
