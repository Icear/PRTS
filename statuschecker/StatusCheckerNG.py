import torch


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # 使用三层
        #   - 卷积层（同时实现不同尺寸图像的输入）
        #   - 池化层（缩小图像尺寸）
        #   - 全连接层
        #   - 分类器输出
        self.conv1 = torch.nn.Conv2d(1, 16, kernel_size=3, stride=2, padding=1)
        self.conv2 = torch.nn.Conv2d(16, 16, kernel_size=3, stride=2, padding=1)
        self.conv3 = torch.nn.Conv2d(16, 10, kernel_size=3, stride=2, padding=1)
        # self.fc = torch.nn.Linear()

    def forward(self, xb):
        xb = torch.nn.functional.relu(self.conv1(xb))
        xb = torch.nn.functional.relu(self.conv2(xb))
        xb = torch.nn.functional.relu(self.conv3(xb))
        xb = torch.nn.functional.adaptive_avg_pool2d(xb, 4)

        return xb.view(-1, xb.size(1))
