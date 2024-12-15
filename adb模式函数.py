import numpy as np
import cv2
import time
import subprocess
import pyscreeze
import mxyr小工具 as mxyr
import os


class 模拟器实例:
    匹配可信度 = 0.9
    重试次数 = 3
    重试延迟 = 1
    加载判定次数 = 2
    截图计数器 = 1
    操作延迟 = 0.5

    def __init__(
        self,
        实例编号: str,
        debug=False,
        log=False,
        日志文件路径="./tmp/log.txt",
        临时文件路径="./tmp/",
        图标路径="./图标",
    ):
        self.实例编号 = 实例编号
        if 实例编号.find(":") == -1:
            self.实例编号_文件名 = 实例编号
        else:
            # 后面路径不允许使用冒号，替换为下划线
            self.实例编号_文件名 = 实例编号.replace(":", "_")
        self.debug = debug
        self.log = log
        self.日志文件路径 = 日志文件路径
        self.临时文件路径 = 临时文件路径
        self.图标路径 = 图标路径
        self.adb指令头 = f"adb -s {实例编号}"
        self.截图文件名 = f"{self.实例编号_文件名}.png"
        self.截图路径 = os.path.join(self.临时文件路径, self.截图文件名)
        self.截图指令 = f"{self.adb指令头} exec-out screencap -p > {self.截图路径}"
        self.分辨率 = self.屏幕分辨率()
        if self.log:
            self.日志文件 = open(self.日志文件路径, "a")
        if self.debug:
            self.打印并写入日志("初始化")
            self.打印并写入日志("实例编号为：" + self.实例编号)
            self.打印并写入日志("debug：" + str(self.debug))
            self.打印并写入日志("log：" + str(self.log))

    def 带时间戳写入日志(self, 写入内容, 时间格式="%Y年%m月%d日 %H时%M分%S秒"):
        self.日志文件.writelines(mxyr.当前时间(时间格式) + "：" + 写入内容 + "\n")

    def 打印并写入日志(self, 写入内容, 时间格式="%Y年%m月%d日 %H时%M分%S秒"):
        print(写入内容)
        if self.log:
            self.带时间戳写入日志(写入内容, 时间格式=时间格式)

    def 图片信息读取(self, 路径: str):
        图片信息 = cv2.imdecode(np.fromfile(路径, dtype=np.uint8), cv2.IMREAD_COLOR)
        if self.debug:
            self.打印并写入日志("读取图片：" + 路径)
        return 图片信息

    def 图片定位(self, 匹配图片: str):
        图片保存路径 = self.截图()
        原始图片 = self.图片信息读取(图片保存路径)
        匹配图片信息 = self.图片信息读取(匹配图片)
        匹配结果 = pyscreeze.locate(
            匹配图片信息, 原始图片, confidence=self.匹配可信度, grayscale=False
        )
        中心坐标 = pyscreeze.center(匹配结果)
        if self.debug:
            self.打印并写入日志(匹配图片 + "中心坐标为：" + str(中心坐标))
        return 中心坐标[0], 中心坐标[1]

    def 截图(self, *保存路径):
        if 保存路径 == ():
            if self.debug:
                文件名 = f"{self.实例编号_文件名}_{self.截图计数器}.png"
                self.截图计数器 += 1
                保存路径 = os.path.join(self.临时文件路径, 文件名)
            else:
                保存路径 = self.截图路径
        else:
            保存路径 = 保存路径[0]
        截图指令 = f"{self.adb指令头} exec-out screencap -p > {保存路径}"
        subprocess.Popen(截图指令, shell=True).wait()
        if self.debug:
            self.打印并写入日志(f"截图成功，文件：{保存路径}")
        return 保存路径

    def 点击(self, x, y):
        x = int(x)
        y = int(y)
        指令 = f"{self.adb指令头} shell input tap {x} {y}"
        subprocess.Popen(指令).wait()
        self.打印并写入日志(f"点击{x},{y}")
        time.sleep(self.操作延迟)

    def 等待_直到找到(self, 图片名称: str, 超时: int):
        图片 = os.path.join(self.图标路径, f"{图片名称}.png")
        起始时间 = time.time()
        耗时 = 0
        while 耗时 < 超时:
            耗时 = time.time() - 起始时间
            try:
                self.打印并写入日志(f"尝试寻找：{图片名称}")
                x坐标, y坐标 = self.图片定位(图片)
                break
            except pyscreeze.ImageNotFoundException:
                self.打印并写入日志(f"未找到图片！正在重试。耗时：{耗时}；超时：{超时}")
                time.sleep(self.重试延迟)
        if 耗时 < 超时:
            self.打印并写入日志(f"找到：{图片名称}；坐标：{x坐标}，{y坐标}")
            return x坐标, y坐标
        else:
            self.打印并写入日志(f"找不到图片（{图片名称}）！超时：{超时}")
            return -1

    def 点击按钮(self, 图标名称, dx=0, dy=0, 次数=1):
        图标 = os.path.join(self.图标路径, f"{图标名称}.png")
        尝试次数 = 0
        while 尝试次数 < self.重试次数:
            try:
                self.打印并写入日志(f"点击按钮：{图标名称}")
                x坐标, y坐标 = self.图片定位(图标)
                break
            except pyscreeze.ImageNotFoundException:
                尝试次数 += 1
                self.打印并写入日志(
                    "未找到图片！正在重试：" + str(尝试次数) + "/" + str(self.重试次数)
                )
                time.sleep(self.重试延迟)
        if 尝试次数 < self.重试次数:
            while 次数 > 0:
                self.点击(x坐标 + dx, y坐标 + dy)
                次数 -= 1
        else:
            self.打印并写入日志(f"失败，找不到图片（{图标名称}）！程序结束！")
            if self.log:
                self.日志文件.close()
            exit()

    def 等待加载(self, 加载图片名称):
        加载图片 = os.path.join(self.图标路径, f"{加载图片名称}.png")
        计数器 = 0
        正在加载 = True
        while 正在加载:
            try:
                (x, y) = self.图片定位(加载图片)
                self.打印并写入日志("加载中，等待···")
                time.sleep(self.重试延迟)
            except pyscreeze.ImageNotFoundException:
                time.sleep(self.重试延迟)
                计数器 += 1
                if 计数器 > self.加载判定次数:
                    正在加载 = False
                else:
                    self.打印并写入日志(
                        "等待确认" + str(计数器) + "/" + str(self.加载判定次数)
                    )

    def 尝试寻找(self, 图片名称: str):
        # 输入图片名称，使用默认图标路径，若找到返回坐标值，若找不到返回-1
        图片 = os.path.join(self.图标路径, f"{图片名称}.png")
        尝试次数 = 0
        while 尝试次数 < self.重试次数:
            try:
                self.打印并写入日志(f"尝试寻找：{图片名称}")
                x坐标, y坐标 = self.图片定位(图片)
                break
            except pyscreeze.ImageNotFoundException:
                尝试次数 += 1
                self.打印并写入日志(
                    "未找到图片！正在重试：" + str(尝试次数) + "/" + str(self.重试次数)
                )
                time.sleep(self.重试延迟)
        if 尝试次数 < self.重试次数:
            self.打印并写入日志(f"找到：{图片名称}；坐标：{x坐标}，{y坐标}")
            return x坐标, y坐标
        else:
            self.打印并写入日志(f"找不到图片（{图片名称}）！")
            return -1

    def 尝试寻找并点击(self, 图片名称):
        查找结果 = self.尝试寻找(图片名称)
        if 查找结果 != -1:
            self.点击(查找结果[0], 查找结果[1])
            return True
        else:
            return False

    def 等待_直到找到并点击(self, 图片名称: str, 超时: int):
        查找结果 = self.等待_直到找到(图片名称, 超时)
        if 查找结果 != -1:
            self.点击(查找结果[0], 查找结果[1])
            return True
        else:
            return False

    def 点击_直到消失(self, 图片名称):
        找到 = True
        while 找到:
            查找结果 = self.尝试寻找(图片名称)
            if 查找结果 == -1:
                找到 = False
            else:
                self.点击(查找结果[0], 查找结果[1])

    def 屏幕分辨率(self):
        指令 = f"{self.adb指令头} shell wm size"
        返回值 = subprocess.Popen(指令, shell=True, stdout=subprocess.PIPE).stdout
        返回值 = 返回值.read().decode("gbk")
        分辨率文字 = 返回值.split(":")[1][1:-2]
        分辨率 = 分辨率文字.split("x")
        return int(分辨率[0]), int(分辨率[1])

    def 返回键(self):
        指令 = f"{self.adb指令头} shell input keyevent 4"
        subprocess.Popen(指令).wait()
        self.打印并写入日志("按返回键")
        time.sleep(self.操作延迟)

    def 向下滚动(self):
        指令 = f"{self.adb指令头} shell input roll 0 200"
        subprocess.Popen(指令).wait()
        if self.debug:
            self.打印并写入日志("向下滚动键")
        time.sleep(self.操作延迟)

    def 滑动(self, x, y, dx, dy, 时间=500):
        x = int(x)
        y = int(y)
        dx = int(dx)
        dy = int(dy)
        指令 = f"{self.adb指令头} shell input swipe {x} {y} {x+dx} {y+dy} {时间}"
        subprocess.Popen(指令).wait()
        self.打印并写入日志(f"滑动，起始点{x}，{y}；滑移{dx}，{dy}，用时：{时间}ms")
        time.sleep(self.操作延迟)

    def 日志关闭(self):
        self.日志文件.close()
