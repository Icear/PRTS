from ctypes import windll

import cv2 as cv
import numpy
import win32api
import win32con
import win32gui
import win32ui


def get_screenshot(hWnd):
    # 获取句柄窗口的大小信息
    left, top, right, bot = win32gui.GetWindowRect(hWnd)
    width = right - left
    height = bot - top
    # 返回句柄窗口的设备环境，覆盖整个窗口，包括非客户区，标题栏，菜单，边框
    hWndDC = win32gui.GetWindowDC(hWnd)
    # 创建设备描述表
    mfcDC = win32ui.CreateDCFromHandle(hWndDC)
    # 创建内存设备描述表
    saveDC = mfcDC.CreateCompatibleDC()
    # 创建位图对象准备保存图片
    saveBitMap = win32ui.CreateBitmap()
    # 为bitmap开辟存储空间
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    # 将截图保存到saveBitMap中
    saveDC.SelectObject(saveBitMap)
    # 保存bitmap到内存设备描述表
    saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
    # opencv+numpy保存
    # 获取位图信息
    signedIntsArray = saveBitMap.GetBitmapBits(True)
    # 内存释放
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hWnd, hWndDC)
    return width, height, signedIntsArray


childHandlerList = []


def main():
    # 通知系统此进程自行处理DPI，避免被缩放影响
    windll.user32.SetProcessDPIAware()

    # 获取后台窗口的句柄，注意后台窗口不能最小化
    hWnd = win32gui.FindWindow(None, "明日方舟 - 星云引擎")  # 窗口的类名可以用Visual Studio的SPY++工具获取
    lParam = win32api.MAKELONG(123, 133)
    # width, height, signedIntsArray = get_screenshot(hWnd)
    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)
    # show_image(width, height, signedIntsArray)

    # 直接拿到子控件，有两个，不知道哪个有点击事件的效果
    win32gui.EnumChildWindows(hWnd, enum_child, None)

    # 发送点击事件


def enum_child(hWnd, param):
    width, height, signedIntsArray = get_screenshot(hWnd)
    # win32gui.SendMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    # win32gui.SendMessage(hWnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)

    print(hWnd, width, height)
    # childHandlerList.append(hWnd)
    return True


def show_image(width, height, signedIntsArray):
    # PrintWindow成功，显示到屏幕
    im_opencv = numpy.frombuffer(signedIntsArray, dtype='uint8')
    im_opencv.shape = (height, width, 4)
    cv.cvtColor(im_opencv, cv.COLOR_BGRA2RGB)
    # cv.imwrite("im_opencv.jpg", im_opencv, [int(cv.IMWRITE_JPEG_QUALITY), 100])  # 保存
    cv.namedWindow('im_opencv', cv.WINDOW_AUTOSIZE | cv.WINDOW_KEEPRATIO)  # 命名窗口
    cv.imshow("im_opencv", im_opencv)  # 显示
    cv.waitKey(0)
    # cv.destroyAllWindows()


if __name__ == '__main__':
    main()
