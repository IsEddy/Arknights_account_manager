import math
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRectF, QRect, QPointF
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QRadialGradient, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton


class SwitchBtn(QWidget):
    checkedChanged = pyqtSignal(bool)
    clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 开关状态，默认关闭
        self.checked = False
        # 可用状态，默认可用
        self.enabled = True
        # 颜色
        self.sliderColorOff = None
        self.sliderColorOn = None
        self.edge = QColor(50, 51, 54)  # 边框颜色
        self.bgColorOff = self.bgColorOn = QColor(255, 255, 255)  # 滑动条颜色
        self.textColorOff = self.textColorOn = QColor(85, 85, 85)  # 文本颜色
        # 初始文本
        self.textOff = ''
        self.textOn = ''
        # 控件边距
        self.space = 2
        # 每次移动的步长为宽度的50分之一
        self.step = self.width() / 50
        # 起始、终点
        self.startX = 0
        self.endX = 0
        # 滑块移动定时器
        self.timer = QTimer()
        self.timer.setInterval(5)
        self.timer.timeout.connect(self.update_slider)
        # 控件可用状态查询
        self.enabled_timer = QTimer()
        self.enabled_timer.setInterval(5)
        self.enabled_timer.timeout.connect(self.update_color)
        self.enabled_timer.start()
        # 字体
        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(9)
        self.setFont(font)

    def set_color(self):
        """滑块形状颜色"""
        # 关闭状态 滑块形状、颜色
        self.sliderColorOff = QRadialGradient(self.width() / 2, self.height() / 2, self.width() / 2, self.width() / 6,
                                              self.height() / 6)
        self.sliderColorOff.setColorAt(0, QColor(0, 0, 0))
        #self.sliderColorOff.setColorAt(0.8, QColor(71, 69, 69))
        # 开启状态 滑块形状、颜色
        self.sliderColorOn = QRadialGradient(self.width() / 2, self.height() / 2, self.width() / 2,
                                             3 * self.width() / 4, self.height() / 2)
        if self.isEnabled():  # 控件可用
            self.edge = QColor(50, 51, 54)  # 边框颜色/红色
            self.sliderColorOn.setColorAt(0, QColor(200, 200, 255))  # 滑块开启时为绿色
            #self.sliderColorOn.setColorAt(0.8, QColor(20, 200, 20))
        else:  # 控件不可用
            self.edge = QColor(141, 141, 141)  # 边框颜色/灰色
            self.sliderColorOn.setColorAt(0, QColor(232, 251, 255))  # 滑块开启时为暗绿色
            #self.sliderColorOn.setColorAt(0.8, QColor(71, 140, 69))

    def update_color(self):
        """刷新控件颜色"""
        self.set_color()
        if self.enabled != self.isEnabled():
            self.enabled = self.isEnabled()
            self.update()

    def resizeEvent(self, event):
        """形状变动时，滑块跟随变动，移动速度变动"""
        self.set_color()
        self.step = self.width() / 35
        self.endX = self.width() - self.height()
        if self.checked:
            self.startX = self.endX
        else:
            self.startX = 0
        self.update()

    def isChecked(self):
        return self.checked

    def setChecked(self, state):
        """设置状态"""
        if self.checked != state:
            self.checked = state
            if self.checked:
                self.endX = self.width() - self.height()
            else:
                self.endX = 0
            self.timer.start()

    def setOffText(self, text):
        self.textOff = text

    def setOnText(self, text):
        self.textOn = text

    def update_slider(self):
        if self.checked:
            if self.startX < self.endX:
                self.startX = self.startX + self.step
            else:
                self.startX = self.endX
                self.timer.stop()
        else:
            if self.startX > self.endX:
                self.startX = self.startX - self.step
            else:
                self.startX = self.endX
                self.timer.stop()

        # 使用贝塞尔曲线函数平滑滑块的运动
        progress = self.startX / (self.width() - self.height())  # 运动进度
        smoothed_progress = self.bezier_easing(progress)  # 使用缓动函数平滑进度

        # 计算新的滑块位置
        self.startX = int(smoothed_progress * (self.width() - self.height()))  # 修改此行，转换为整数

        self.update()

    def bezier_easing(self, t):
        # 使用四次贝塞尔曲线函数，调整控制点以实现不同的速度曲线
        p0 = 0
        p1 = 0.3
        p2 = 0.7
        p3 = 1

        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3

    def mousePressEvent(self, event):
        self.checked = not self.checked
        # 发射信号
        self.checkedChanged.emit(self.checked)
        # 状态切换改变后自动计算终点坐标
        if self.checked:
            self.endX = self.width() - self.height()
        else:
            self.endX = 0
        self.timer.start()

    def mouseReleaseEvent(self, event):
        self.clicked.emit("self")

    def paintEvent(self, evt):
        # 绘制准备工作, 启用反锯齿
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 绘制背景
        self.draw_back(painter)
        # 绘制滑块
        self.draw_slider(painter)
        # 绘制文字
        self.draw_text(painter)
        painter.end()

    def draw_text(self, painter):
        painter.save()
        if self.checked:
            painter.setPen(self.textColorOn)
            rect = QRect(int(0 - self.width() / 2), -1, int(self.width() * 2) - self.space, self.height())
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignCenter, self.textOn)
        else:
            painter.setPen(self.textColorOff)
            rect = QRect(int(0 - self.width() / 2), -1, int(self.width() * 2) - self.space, self.height())
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignCenter, self.textOff)
        painter.restore()

    def draw_back(self, painter):
        painter.save()
        pen = QPen(self.edge)
        pen.setWidth(1)  # 设置线条粗细
        painter.setPen(pen)
        if self.checked:
            painter.setBrush(self.bgColorOn)
        else:
            painter.setBrush(self.bgColorOff)
        rect = QRect(0, 0, self.width(), self.height())
        # 半径为高度的一半
        radius = rect.height() / 2
        # 圆的宽度为高度
        circle_width = rect.height()
        path = QPainterPath()
        path.moveTo(radius, rect.left())
        path.arcTo(QRectF(rect.left(), rect.top(), circle_width, circle_width), 90, 180)
        path.lineTo(rect.width() - radius, rect.height())
        path.arcTo(QRectF(rect.width() - rect.height(), rect.top(), circle_width, circle_width), 270, 180)
        path.lineTo(radius, rect.top())
        painter.drawPath(path)
        painter.restore()

    def draw_slider(self, painter):
        painter.save()
        if self.checked:
            pen = QPen()
            pen.setColor(QColor(0, 0, 0))  # 设置线条颜色
            pen.setWidth(1)  # 设置线条粗细
            painter.setPen(pen)
            painter.setBrush(self.sliderColorOn)
        else:
            painter.setBrush(self.sliderColorOff)
        rect = QRect(0, 0, self.width(), self.height())
        slider_width = rect.height() - self.space * 2
        slider_x = int(self.startX + self.space * 1)
        slider_y = int(self.space * 1)
        slider_rect = QRect(slider_x, slider_y, slider_width, slider_width)
        painter.drawEllipse(slider_rect)
        painter.restore()

class InvisibleButton(QPushButton):
    # 自定义一个clicked信号，用于传递按钮的文本
    clicked = pyqtSignal(str)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        # 设置按钮的大小为100x50
        self.setFixedSize(3, 3)
        # 设置按钮的文字、字体、颜色等属性
        self.text = text
        self.setFont(QFont("Arial", 16))
        self.setColor(QColor(255, 255, 255))
        # 设置按钮的状态为未按下
        self.pressed = False

    def setColor(self, color):
        self.color = color

    def paintEvent(self, event):
        # 创建一个画笔对象
        painter = QPainter(self)
        # 设置画笔的抗锯齿效果
        painter.setRenderHint(QPainter.Antialiasing)
        # 设置画笔的颜色为白色
        painter.setPen(Qt.white)
        # if self.pressed:
        #     brush = QBrush(QColor(0, 0, 0))
        # else:
        #     brush = QBrush(QColor(0, 0, 0))
        # painter.setBrush(brush)
        # 绘制一个圆角矩形，作为按钮的外观
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 1, 1)
        # 设置画笔的字体和颜色
        painter.setFont(self.font())
        painter.setPen(self.color)
        # 绘制按钮的文字，居中对齐
        painter.drawText(0, 0, self.width(), self.height(), Qt.AlignCenter, self.text)

    def mousePressEvent(self, event):
        # 如果鼠标左键按下，设置按钮的状态为按下，并更新界面
        if event.button() == Qt.LeftButton:
            self.pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        # 如果鼠标左键释放，设置按钮的状态为未按下，并更新界面
        if event.button() == Qt.LeftButton:
            self.pressed = False
            self.update()
            # 发射自定义的clicked信号，传递按钮的文本
            self.clicked.emit(self.text)