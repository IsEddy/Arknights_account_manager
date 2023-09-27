import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timedelta

import cv2
import psutil
import qdarktheme
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QDoubleValidator, QTextCharFormat, QColor, QTextCursor
from PyQt5.QtWidgets import QFormLayout, QDialog, QLineEdit, QTimeEdit, QApplication, QCheckBox, QPushButton, \
    QMessageBox, QComboBox, QPlainTextEdit, QHBoxLayout

from asst.asst import Asst
from asst.emulator import Bluestacks  # MAA的集成，用于获取蓝叠的adbport
from asst.skyland import *  # 森空岛签到，by xxyz30
from asst.switchbutton import SwitchBtn, InvisibleButton  # 自定义的两个按钮库
from asst.utils import InstanceOptionType  # MAA的集成，用于肉鸽

if not os.path.exists('debug'):
    os.makedirs('debug')
logging.basicConfig(filename='./debug/debug.log', level=logging.DEBUG,
                    format='[%(asctime)s] - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger('main')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # 设置控制台处理器的级别
console_handler.setFormatter(logging.Formatter('[%(asctime)s] - %(name)s - %(levelname)s: %(message)s'))
logger.addHandler(console_handler)


group_count = 1
theme = 'light'
app_name = '斯卡蒂账号小助手'  # 程序名
sim_name = 'ld'  # 什么模拟器
sleeptime = 60  # 多少s检测一次时间
rogue_name = 'Sami'
adb_path = ''
adb_port = ''
pre_input = ''
tapdelay = 3
do_count = 0  # 用于一键清日常的计数
if_debug = False
version = 0.11
is_running = False


class PrintOutput(QPlainTextEdit):  # print重写
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.cache = ""
        font = QFont("Courier New", 10)  # 使用Courier New字体，大小为10
        self.setFont(font)

    def write(self, text):
        self.cache += text
        if text.endswith('\n'):
            current_time = datetime.now().strftime("%m-%d %H:%M:%S")
            text_with_time = f"{current_time} {self.cache}"
            self.cache = ""

            cursor = self.textCursor()
            cursor.movePosition(cursor.End)
            format = QTextCharFormat()
            if hasattr(self, 'is_error') and self.is_error:  # 错误输出为红色
                format.setForeground(QColor("red"))
            cursor.setCharFormat(format)
            cursor.insertText(text_with_time)
            cursor.insertText('\n')
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
    def flush(self):
        pass

def print_error(*args, **kwargs):
    # Set is_error attribute to True when calling print_error
    if 'file' not in kwargs:
        kwargs['file'] = sys.stdout
    kwargs['file'].is_error = True
    print(*args, **kwargs)
    # Reset is_error attribute to False
    kwargs['file'].is_error = False


class TimerThread(QThread):  # 多线程，用于账号切换
    timer_signal = pyqtSignal(str)
    signal_start_rogue = pyqtSignal()

    def __init__(self, account, password, if_rogue: bool, group):
        super().__init__()
        self.account = account
        self.password = password
        self.if_rogue = if_rogue
        self.group = group

    def run(self):  # 换号主函数
        global is_running, adb_path, tapdelay, sim_name, adb_port, pre_input, path
        is_running = True
        logger.debug("[Child Thread]Account change thread start!")
        dialog = InputDialog()
        account = self.account
        password = self.password
        if_rogue = self.if_rogue
        group = self.group
        # 终止MAA
        print("尝试终止MAA ...")
        logger.debug("[Child Thread]Killing MAA...")
        popen = os.popen('wmic process where name="maa.exe" call terminate 2>&1').read()
        logger.debug(popen)
        try:
            asst.stop()
        except:
            pass
        if dialog.rogue_timer.isActive():
            dialog.rogue_timer.stop()
        tapdelay = float(dialog.tapdelay.text())
        t = tapdelay
        i = None
        logger.debug("[Child Thread]Connecting simulator...")
        print("正在接模拟器")
        subprocess.run(''.join([adb_path + ' connect ' + adb_port]), shell=True)
        popen = os.popen(''.join([adb_path + ' devices']))  # 有几率出问题？？？
        if sim_name == 'bluestacks':
            subprocess.run(''.join([pre_input + 'input su']), shell=True)
        print("成功连接至", dialog.sim_name.currentText())
        logger.debug("[Child Thread]Successfully connect to simulator.")
        time.sleep(2)
        logger.debug("[Child Thread]Killing 自动精灵...")
        try:
            subprocess.run(''.join([pre_input, 'am force-stop com.zdanjian.zdanjian']), shell=True)  # 关闭自动精灵(你可以用自动精灵，不会出事)
        except:
            pass
        time.sleep(2)
        size = os.popen(pre_input + 'wm size').read()
        size = size[size.find(":") + 2:]
        size_x = int(size[:  size.find("x")])
        size_y = int(size[size.find("x") + 1:])
        print('当前分辨率：' + ''.join([str(size_x), "x", str(size_y)]))
        logger.debug('[Child Thread]Current resolution：' + ''.join([str(size_x), "x", str(size_y)]))
        print(f"开始切换至账号 {account}")
        logger.debug(f"[Child Thread]Start switching to account {account}...")
        with open("./recognition_dataset/recg.json", "r") as f:
            data = json.load(f)
            f.close()
        while True:
            logger.debug("[Child Thread]Executing image recognition...")
            img = dialog.capture_screen()
            found_match = False  # 用于跟踪是否已经有一次判断成立
            begin_login = False  # 用于跟踪是否开始登录
            for images in data:
                if img is None:
                    break
                template = cv2.imread('./recognition_dataset/' + images["image"])
                # template = cv2.resize(template, (size_x, size_y))
                result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                if result.max() > float(images["threshold"]):
                    logger.debug("[Child Thread]In threshold: " + images["threshold"])
                    logger.debug("[Child Thread]" + images["image"] + " matched")
                    found_match = True
                    taps = images["taps"].split(";")  # 点击的坐标使用分号分隔开
                    for point in taps:
                        if point == "exit":  # 坐标支持特殊项：exit，作用为结束识图步骤，开始输入账号密码
                            begin_login = True
                        elif point == "open_game":
                            logger.debug("[Child Thread]Starting Arknights...")
                            run_command(
                                pre_input + 'monkey -p com.hypergryph.arknights -c android.intent.category.LAUNCHER 1')
                            # 打开!方舟
                        else:
                            tap_point(pre_input, int(point.split(",")[0]), int(point.split(",")[1]),
                                             size_x, size_y)
                            time.sleep(t)
                    break
                # else:
                #     logger.debug("In threshold: " + images["threshold"])
                #     logger.debug(images["image"] + " Not matched")
            if not found_match:
                # 没找到就返回
                tap_point(pre_input, 1, 5, size_x, size_y)  # 1！5！
                run_command(pre_input + 'input keyevent BACK')  # 返回
                logger.debug("[Child Thread]No match found")
                logger.debug("[Child Thread]Adb execute back.")
                time.sleep(t)
            if begin_login:
                logger.debug("[Child Thread]Start to input account and password.")
                break
        tap_point(pre_input, 900, 415, size_x, size_y)  # 输入账号
        time.sleep(t)
        run_command(pre_input + 'input text ' + account)
        time.sleep(t)
        tap_point(pre_input, 900, 540, size_x, size_y)  # 输入密码
        time.sleep(t)
        run_command(pre_input + 'input text ' + password)
        time.sleep(t)
        tap_point(pre_input, 705, 620, size_x, size_y)
        time.sleep(t)
        tap_point(pre_input, 960, 750, size_x, size_y)
        time.sleep(t)
        # 终止adb
        logger.debug("[Child Thread]Disconnecting adb...")
        run_command(adb_path + ' disconnect')
        time.sleep(2)
        # print("尝试终止adb ...")
        # logger.debug("[Child Thread]Killing adb.exe...")  # 似乎不终止adb更好?
        # popen = os.popen('taskkill /pid adb.exe /f 2>&1').read()
        # print(popen)
        # if popen[:2] == "错误":
        #     print("终止adb失败，用管理员方式打开试试？")
        #     logger.debug("[Child Thread]Disconnect adb failed")
        # else:
        #     logger.debug("[Child Thread]Disconnect adb succeeded")
        logger.debug("[Child Thread]Shutting down RuntimeBroker.exe...")
        run_command('taskkill /pid RuntimeBroker.exe /f')
        # 启动MAA
        time.sleep(2)
        print("正在启动MAA")
        logger.debug("[Child Thread]Starting MAA...")
        with open(''.join(str(path) + '\config\gui.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            if ''.join(['account', str(group)]) in data['Configurations']:
                logger.debug("[Child Thread]Custom config found!")
                command = ''.join(
                    [str(pathlib.Path(__file__).parent.parent), r"\maa.exe --config ", 'account', str(group)])
                logger.debug("[Child Thread]Start MAA in config account" + str(group))
            elif 'main' in data['Configurations']:
                command = ''.join([str(pathlib.Path(__file__).parent.parent), r"\maa.exe --config main"])
                logger.debug("[Child Thread]Start MAA in config main")
            else:
                command = ''.join([str(pathlib.Path(__file__).parent.parent), r"\maa.exe"])
                logger.debug("[Child Thread]Start MAA in Default config")
            subprocess.Popen(command)
            f.close()
        if if_rogue and dialog.rogue_timer.isActive() is False:  # 开启肉鸽定时器
            logger.debug("[Child Thread]Start Rogue timer!")
            self.signal_start_rogue.emit()
        with open(''.join([str(pathlib.Path(__file__).parent.parent), r'\MAA.Judge']), "r") as f:
            judge = f.read()
            f.close()
        while judge == "Stop":
            with open(''.join([str(pathlib.Path(__file__).parent.parent), r'\MAA.Judge']), "r") as f:
                judge = f.read()
                f.close()
        logger.debug("[Child Thread]Task Complete")
        is_running = False

    def stop(self):
        self.is_running = False


def get_process_path(process_name):  # 获取进程的绝对位置
    global sim_name
    if process_name != 'default':
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                path1 = os.path.abspath(proc.exe())
                path2 = pathlib.Path(path1).parent
                if sim_name == 'ld' or sim_name == 'mumu12' or sim_name == 'nox':
                    path1 = ''.join([str(path2), r'\adb.exe'])  # 雷电的adb路径
                elif sim_name == 'bluestacks':
                    path1 = ''.join([str(path2), r'\HD-Adb.exe'])
                elif sim_name == 'mumu':
                    path1 = ''.join([str(path2.parent), r'\vmonitor\bin\adb_server.exe'])
                path1 = r''.join(['"', path1, '"'])
                return path1
        path1 = ''.join([str(pathlib.Path(__file__).parent.parent), r'\adb\platform-tools\adb.exe'])
        path1 = r''.join(['"', path1, '"'])
        return path1
    else:
        path1 = ''.join([str(pathlib.Path(__file__).parent.parent), r'\adb\platform-tools\adb.exe'])
        path1 = r''.join(['"', path1, '"'])
        return path1


def tap_point(pre_input, x, y, size_x, size_y):
    x = str(int((x / 1920) * size_x))
    y = str(int((y / 1080) * size_y))
    run_command(pre_input + 'input tap ' + x + " " + y)
    logger.debug("Tap " + x + " " + y)
    return None


def run_command(commands):
    subprocess.Popen(commands, shell=True)  # 用于无终端执行代码


class InputDialog(QDialog):

    def capture_screen(self, img=None):  # 截图函数，返回模拟器状态
        global adb_path, sim_name, adb_port
        dump_path = ''.join([str(pathlib.Path(__file__).parent), r'\recognition_dataset'])
        logger.debug("Delete image cache")
        run_command("del " + dump_path + r"\ss.png")
        run_command(
            pre_input + "rm /sdcard/ss.png")
        logger.debug("Capture image")
        run_command(
            pre_input + "screencap -p /sdcard/ss.png")
        time.sleep(1)  # adb: error:
        i = 0
        while True:
            logger.debug("Pulling image to dump path")
            time.sleep(1)
            if sim_name == 'ld':
                popen = os.popen(
                    adb_path + " -s emulator-5554 pull /sdcard/ss.png " + dump_path).read()
            elif sim_name == 'nox':
                popen = os.popen(
                    adb_path + " pull /sdcard/ss.png " + dump_path).read()
            elif sim_name == 'mumu':
                popen = os.popen(
                    adb_path + " pull /sdcard/ss.png " + dump_path).read()
            elif sim_name == 'mumu12':
                popen = sos.popen(
                    adb_path + " pull /sdcard/ss.png " + dump_path).read()
            elif sim_name == 'bluestacks':
                popen = os.popen(
                    adb_path + " -s " + adb_port + " pull /sdcard/ss.png " + dump_path).read()
            else:
                popen = os.popen(
                    adb_path + " pull /sdcard/ss.png " + dump_path).read()
            logger.debug(popen)
            if popen.startswith("adb: error:") is False:
                break
            elif i >= 10:
                logger.error("Reached the maximum retry limit, capture again.")
                run_command(
                    pre_input + "screencap -p /sdcard/ss.png")
                i = 0
            else:
                i += 1
                logger.error(f"Failed to pull image, retrying {i} times")
        logger.debug("Loading image...")
        img = cv2.imread(dump_path + r'\ss.png')
        i = 0
        while img is None or img.size == 0:
            i += 1
            logger.error(f"Loading image failed! Retrying count {i}...")
            img = cv2.imread(dump_path + r'\ss.png')
            logger.debug(f"Wait {tapdelay}second to load image...")
            time.sleep(1)
            if i == 10:
                logger.error("Reached the maximum retry limit.")
                print_error("截图失败！")
                return None
        img = cv2.resize(img, (1920, 1080))
        return img
        # template = cv2.imread('./recognition_dataset/12+.png')
        # result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        # if result.max() > 0.8:
        #     return '位于开始页'

    def __init__(self):
        global app_name, adb_path

        super().__init__()
        main_layout = QHBoxLayout(self)
        self.setWindowTitle(app_name)
        self.form = QFormLayout(self)
        self.inputs = []  # 存储每组输入框的列表

        self.add_button = QPushButton("添加账号", self)
        self.add_button.clicked.connect(self.add_input)
        self.del_button = QPushButton("删除账号", self)
        self.del_button.clicked.connect(self.del_input)

        self.start_btn = QPushButton('      开始！       ', self)
        self.start_btn.clicked.connect(self.start_command)
        self.stop_btn = QPushButton('       停！        ', self)
        self.stop_btn.clicked.connect(self.stop_command)

        self.change_btn = QPushButton('切换 暗黑/白昼 模式', self)
        self.change_btn.clicked.connect(self.change_command)

        self.rogue_btn = QPushButton('手动开始打肉鸽', self)
        self.rogue_btn.clicked.connect(self.start_rogue)

        self.hidden_btn = InvisibleButton("deeebuuuggg", self)
        self.hidden_btn.clicked.connect(self.deeebuuuggg)

        self.one_key = QPushButton('一键全部清日常', self)
        self.one_key.clicked.connect(self.one_key_btn_command)

        self.tapdelay = QLineEdit()
        self.tapdelay.setText("3")
        self.cpdtext = "输入合适的点击后置延时"

        validator = QDoubleValidator(self)
        validator.setNotation(QDoubleValidator.StandardNotation)  # 使用标准表示法
        validator.setBottom(0.5)  # 最小值
        validator.setTop(9)  # 最大值
        self.tapdelay.setValidator(validator)

        self.sim_name = QComboBox(self)
        self.sim_name.addItems(['雷电模拟器', 'MuMu 模拟器', 'MuMu 模拟器 12', '蓝叠模拟器', '夜神模拟器', '通用模式'])
        self.sim_name.currentIndexChanged.connect(self.change_adb_path)

        self.setWindowFlag(Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint)

        icon = QIcon("skadi.ico")
        self.setWindowIcon(icon)  # 设置图标
        self.form.addRow("请选择你的模拟器", self.sim_name)

        self.load_info()  # 加载info.txt文件中的数据

        self.output_text_edit = PrintOutput()

        # 将QForm和PrintOutput添加到水平布局中
        main_layout.addLayout(self.form)
        main_layout.addWidget(self.output_text_edit)

        self.setLayout(main_layout)

        self.sign_timer = QTimer(self)
        self.sign_timer.timeout.connect(lambda: self.skyland_sign())
        self.sign_timer.start(40 * 1000)

        self.rogue_timer = QTimer(self)
        self.account_timer = QTimer(self)

    def redirect_print_to_widget(self):
        sys.stdout = self.output_text_edit

    def restore_print(self):
        sys.stdout = sys.__stdout__

    def change_adb_path(self):
        global sim_name, adb_path, adb_port, pre_input
        if self.sim_name.currentText() == '雷电模拟器':
            sim_name = 'ld'
            adb_port = '127.0.0.1:5555'
            adb_path = get_process_path('dnplayer.exe')
            pre_input = ''.join([adb_path + ' -s emulator-5554 shell '])
            # pre_input = ''.join([adb_path + ' -s 127.0.0.1:5555 shell '])
        elif self.sim_name.currentText() == 'MuMu 模拟器':
            sim_name = 'mumu'
            adb_port = '127.0.0.1:7555'
            adb_path = get_process_path('NemuPlayer.exe')
            pre_input = ''.join([adb_path + ' shell '])
        elif self.sim_name.currentText() == 'MuMu 模拟器 12':
            sim_name = 'mumu12'
            adb_path = get_process_path('MuMuPlayer.exe')
            if adb_path[:1] == '"':
                adb_port = os.popen(str(pathlib.Path(adb_path).parent) + r'\MuMuManager.exe" adb -v 0').read()
            else:
                adb_port = os.popen(str(pathlib.Path(adb_path).parent) + r'\MuMuManager.exe adb -v 0').read()
            if adb_port == '':
                logger.error('Failed to get mumu12 adb port')
                print_error("获取mumu12模拟器adb端口失败！")
                adb_port = '127.0.0.1:5555'
            pre_input = ''.join([adb_path + ' shell '])
        elif self.sim_name.currentText() == '蓝叠模拟器':
            sim_name = 'bluestacks'
            try:
                adb_port = Bluestacks.get_hyperv_port(r"C:\ProgramData\BlueStacks_nxt\bluestacks.conf", "Pie64_1")
            except:
                logger.error('Failed to get bluestacks adb port')
                print_error("获取蓝叠模拟器adb端口失败！")
                adb_port = '127.0.0.1:5555'
            adb_path = get_process_path('HD-Player.exe')
            pre_input = ''.join([adb_path + ' -s ' + adb_port + ' shell '])
        elif self.sim_name.currentText() == '夜神模拟器':
            sim_name = 'nox'
            adb_port = '127.0.0.1:62001'
            adb_path = get_process_path('nox.exe')
            pre_input = ''.join([adb_path + ' shell '])
        elif self.sim_name.currentText() == '通用模式':
            sim_name = 'default'
            adb_port = '127.0.0.1:5555'
            adb_path = get_process_path('default')
            pre_input = ''.join([adb_path + ' shell '])
        logger.debug(f"Using simulator: {self.sim_name.currentText()}")
        logger.debug(f"Set adb path: {adb_path}")
        logger.debug(f"Set adb port: {adb_port}")
        logger.debug(f"Using pre input: {pre_input}")

        print('设置模拟器为：', self.sim_name.currentText(), '\n'
                                                      'Adb路径：', adb_path)

    def deeebuuuggg(self):
        global sleeptime, if_debug
        if not if_debug:
            for i, input_group in enumerate(self.inputs):
                password_edit = input_group[1]
                password_edit.setEchoMode(QLineEdit.Normal)
            if_debug = True
            sleeptime = 1
            print(f"检测时间调整为{sleeptime}，密码已显示，debug模式开启")
        else:
            for i, input_group in enumerate(self.inputs):
                password_edit = input_group[1]
                password_edit.setEchoMode(QLineEdit.Password)
            if_debug = False
            sleeptime = 60
            print(f"检测时间调整为{sleeptime}，密码已隐藏，debug模式关闭")

    def add_input(self):
        global group_count
        account_edit = QLineEdit(self)  # 创建账号输入框
        password_edit = QLineEdit(self)
        password_edit.setEchoMode(QLineEdit.Password)  # 创建密码输入框
        time_edit = QTimeEdit(self)  # 创建时间输入框
        time_edit.setDisplayFormat('HH:mm')
        time_edit.setCalendarPopup(True)
        if_rogue = QCheckBox(self)
        if_rogue.clicked.connect(self.switch_btn_command)
        rogue_name = QComboBox(self)
        rogue_name.addItems(['萨米', '水月', '傀影'])
        switch = SwitchBtn()
        switch.setOnText("账号已开启！")
        switch.setOffText("账号已关闭！")
        switch.clicked.connect(self.switch_btn_command)
        switch.setChecked(1)

        input_group = (account_edit, password_edit, time_edit, if_rogue, rogue_name, switch)  # 将一组输入框打包为一个元组
        self.inputs.append(input_group)
        self.save_info()  # 保存info.txt文件中的数据

        with open("info.txt", "r") as f:

            data = json.load(f)  # 加载json格式的数据为字典对象
            for group in data:
                # print(group["group"])
                if group["group"] == group_count:
                    account = group["account"]
                    password = group["password"]
                    time = group["time"]  # 获取时间
                    rogue = bool(group["if_rogue"])
                    rogue_number = group["rogue_name"]  # 0为萨米，1为水月，2为愧影
                    account_switch = group["switch"]
                    account_edit = QLineEdit(self)
                    account_edit.setText(account)
                    password_edit = QLineEdit(self)
                    password_edit.setEchoMode(QLineEdit.Password)
                    password_edit.setText(password)
                    time_edit = QTimeEdit(self)
                    time_edit.setTime(QTime(int(time[0:2]), int(time[3:5])))
                    time_edit.setDisplayFormat('HH:mm')
                    time_edit.setCalendarPopup(True)
                    if_rogue = QCheckBox(self)
                    if_rogue.setText('任务完毕后打肉鸽')
                    if_rogue.setChecked(rogue)
                    if_rogue.clicked.connect(self.switch_btn_command)
                    rogue_name = QComboBox(self)
                    rogue_name.addItems(['萨米', '水月', '傀影'])
                    rogue_name.setCurrentIndex(rogue_number)
                    switch = SwitchBtn()
                    switch.setOnText("账号已开启！")
                    switch.setOffText("账号已关闭！")
                    switch.clicked.connect(self.switch_btn_command)
                    switch.setChecked(account_switch)

                    account_label = f"第{group_count}组账号密码:"  # 创建账号标签
                    time_lable = "执行时间:"
                    account_edit = input_group[0]  # 获取信息
                    password_edit = input_group[1]
                    time_edit = input_group[2]
                    self.form.addRow(account_label, switch)  # 添加布局
                    self.form.addRow(account_edit, password_edit)
                    self.form.addRow(time_lable, time_edit)
                    self.form.addRow(if_rogue, rogue_name)
        self.form.addRow(self.start_btn, self.add_button)
        self.form.addRow(self.stop_btn, self.del_button)
        self.form.addRow(self.change_btn, self.rogue_btn)
        self.form.addRow(self.one_key)
        self.form.addRow(self.cpdtext, self.tapdelay)

        group_count += 1

    def del_input(self):
        global group_count
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("删除账号")
        msg.setText("您确定要删除最后一组账号吗？" + '\n' + "（程序将会重启一下）")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        choice = msg.exec_()
        if choice == QMessageBox.Yes:
            group_count -= 2
            with open("info.txt", "r+") as f:
                data = json.load(f)
                if data:
                    data.pop()  # 如果列表不为空，删除最后一个元素
                f.truncate(0)
                f.seek(0)
                json.dump(data, f, indent=4)  # 清空文件并写入
                f.close()
            group_count += 1
            exe_path = sys.executable
            # 暂停一段时间，确保当前进程结束
            time.sleep(1)
            # 使用os.execl()来重启程序
            os.execl(exe_path, exe_path, *sys.argv[1:])

    def load_info(self):
        global group_count
        # 加载info.txt文件中的数据的函数
        if os.path.exists("info.txt"):  # 如果之前保存了
            default_values = {  # json所有键以及默认键值
                "group": 1,
                "account": "",
                "password": "",
                "time": "00:00",
                "if_rogue": False,
                "rogue_name": 0,
                "switch": True
            }
            with open("info.txt", "r") as f:
                self.inputs = []
                data = json.load(f)
                for item in data:  # 遍历每个项，检查并添加缺失的键值
                    for key, value in default_values.items():
                        if key not in item:
                            item[key] = value
                for group in data:
                    account = group["account"]  # 获取数据
                    password = group["password"]
                    time = group["time"]
                    rogue = bool(group["if_rogue"])
                    rogue_number = group["rogue_name"]  # 0为萨米，1为水月，2为愧影
                    account_switch = group["switch"]
                    account_edit = QLineEdit(self)
                    account_edit.setText(account)
                    password_edit = QLineEdit(self)
                    password_edit.setEchoMode(QLineEdit.Password)
                    password_edit.setText(password)
                    time_edit = QTimeEdit(self)
                    time_edit.setTime(QTime(int(time[0:2]), int(time[3:5])))
                    time_edit.setDisplayFormat('HH:mm')
                    time_edit.setCalendarPopup(True)
                    if_rogue = QCheckBox(self)
                    if_rogue.setText('任务完毕后打肉鸽')
                    if_rogue.setChecked(rogue)
                    if_rogue.clicked.connect(self.switch_btn_command)
                    rogue_name = QComboBox(self)
                    rogue_name.addItems(['萨米', '水月', '傀影'])
                    rogue_name.setCurrentIndex(rogue_number)
                    switch = SwitchBtn()
                    switch.setOnText("账号已开启！")
                    switch.setOffText("账号已关闭！")
                    switch.clicked.connect(self.switch_btn_command)
                    switch.setChecked(account_switch)

                    input_group = (
                        account_edit, password_edit, time_edit, if_rogue, rogue_name, switch)  # 将一组输入框打包为一个元组
                    self.inputs.append(input_group)  # 将一组输入框添加到列表中
                    group_count += 1

        else:  # 如果第一次打开
            group_count = len(self.inputs) + 1  # 计算当前输入框的组数
            account_edit = QLineEdit(self)
            password_edit = QLineEdit(self)
            password_edit.setEchoMode(QLineEdit.Password)
            time_edit = QTimeEdit(self)
            time_edit.setDisplayFormat('HH:mm')
            time_edit.setCalendarPopup(True)
            if_rogue = QCheckBox(self)
            if_rogue.clicked.connect(self.switch_btn_command)
            if_rogue.setText('任务完毕后打肉鸽')

            rogue_name = QComboBox(self)
            rogue_name.addItems(['萨米', '水月', '傀影'])
            switch = SwitchBtn()
            switch.setOnText("账号已开启！")
            switch.setOffText("账号已关闭！")
            switch.clicked.connect(self.switch_btn_command)
            switch.setChecked(1)

            input_group = (account_edit, password_edit, time_edit, if_rogue, rogue_name, switch)  # 将一组输入框打包为一个元组
            self.inputs.append(input_group)  # 将一组输入框添加到列表中

        self.showshow()
        self.save_info()

    def save_info(self):
        global group_count
        # 保存info.txt文件中的数据的函数
        group_count = 0
        data = []  # 创建一个空列表用于存储数据
        for i, input_group in enumerate(self.inputs):  # 遍历列表中的每一组输入框
            group_count += 1
            account_edit = input_group[0]  # 获取数据
            password_edit = input_group[1]
            time_edit = input_group[2]
            if_rogue = input_group[3]
            rogue_name = input_group[4]
            switch = input_group[5]
            account = account_edit.text()
            password = password_edit.text()
            time = time_edit.text()
            if_rogue = if_rogue.isChecked()
            rogue_name = rogue_name.currentIndex()
            account_switch = switch.isChecked()
            group_data = {"group": group_count, "account": account, "password": password, "time": time,
                          "if_rogue": if_rogue, "rogue_name": rogue_name, "switch": account_switch}  # 将一组数据打包为一个字典对象
            data.append(group_data)  # 将一组数据添加到列表中

        with open("info.txt", "w") as f:
            json.dump(data, f, indent=4)

    def showshow(self):  # 显示函数
        # 显示
        for i, input_group in enumerate(self.inputs):  # 遍历列表中的每一组输入框
            group = i + 1  # 计算当前输入框的组数
            account_label = f"第{group}组账号密码:"
            time_lable = "执行时间:"
            account_edit = input_group[0]
            password_edit = input_group[1]
            time_edit = input_group[2]
            if_rogue = input_group[3]
            rogue_name = input_group[4]
            switch = input_group[5]
            self.form.addRow(account_label, switch)
            self.form.addRow(account_edit, password_edit)
            self.form.addRow(time_lable, time_edit)
            self.form.addRow(if_rogue, rogue_name)
        self.form.addRow(self.start_btn, self.add_button)
        self.form.addRow(self.stop_btn, self.del_button)
        self.form.addRow(self.change_btn, self.rogue_btn)
        self.form.addRow(self.one_key)
        self.form.addRow(self.cpdtext, self.tapdelay)

    def switch_btn_command(self):
        self.save_info()
        if self.account_timer.isActive():
            self.stop_command()
            self.start_command()

    def one_key_btn_command(self):
        global do_count
        logger.debug("One key timer start!")
        print("一键清理智开始")
        do_count = 0
        with open("info.txt", "r") as f:
            times = {}
            data = json.load(f)  # 加载json格式的数据为字典对象
            i = 0
            for group in data:  # 遍历字典中的每一组数据
                account = group["account"]
                password = group["password"]
                rogue_name = group["rogue_name"]  # 0为萨米，1为水月，2为愧影
                account_switch = group["switch"]
                if account_switch:
                    i += 1
                    if rogue_name == 0:
                        rogue_name = "Sami"
                    elif rogue_name == 1:
                        rogue_name = "Mizuki"
                    elif rogue_name == 2:
                        rogue_name = "Phantom"
                    times[i] = [account, password, False, group["group"]]
        self.one_key_timer = QTimer(self)
        self.one_key_timer.timeout.connect(lambda: self.one_key_command(times))
        self.one_key_timer.start(sleeptime * 1000)

    def one_key_command(self, times):
        global do_count, group_count
        self.save_info()
        self.setWindowTitle(app_name + '：开始运行！')
        with open(''.join([str(pathlib.Path(__file__).parent.parent), r'\MAA.Judge']), "r") as f:
            judge = f.readlines()[-1]
            logger.debug(f"[One Key Timer]Detect MAA:{judge}")
            print(f'MAA当前状态：{judge}')
            f.close()
        for i in times:
            if judge == 'Stop' and do_count == i-1:
                timer_thread = TimerThread(times[i][0], times[i][1], times[i][2], times[i][3])
                if is_running is False:
                    do_count += 1
                    print(f"执行账号：{times[i][0]}!")
                    timer_thread.start()
                time.sleep(2)

                if do_count == group_count:
                    logger.info("[One Key Timer]All account complete!")
                    print("所有账号执行完毕！")
                    self.one_key_timer.stop()

    def start_command(self):  # 开始按钮
        logger.debug("Account timer start!")
        print("将执行以下账号：")
        self.save_info()
        self.setWindowTitle(app_name + '：开始运行！')
        if self.account_timer.isActive():
            self.account_timer.stop()
        with open("info.txt", "r") as f:
            times = {}  # 创建一个空字典，用于存放时间和对应的数据
            data = json.load(f)  # 加载json格式的数据为字典对象
            i = 0
            for group in data:  # 遍历字典中的每一组数据
                i += 1
                account = group["account"]
                password = group["password"]
                time = group["time"]
                rogue = group["if_rogue"]
                rogue_name = group["rogue_name"]  # 0为萨米，1为水月，2为愧影
                account_switch = group["switch"]
                if i == 1:
                    run_command(r'schtasks /create /tn "WakeUp" /tr "C:\Windows\System32\cmd.exe /c ECHO '+'WakeUp'+' & pause" /sc ones /st ' + time)
                    logger.info(f"Create Windows WakeUp task at time {time}.")
                    print("根据最早的启动时间新建了Windows唤醒任务！")
                if account_switch:
                    if rogue_name == 0:
                        rogue_name = "Sami"
                    elif rogue_name == 1:
                        rogue_name = "Mizuki"
                    elif rogue_name == 2:
                        rogue_name = "Phantom"
                    times[time] = [account, password, rogue, rogue_name, i]
                    print(f'第{i}组账号：', account, '\n'
                            '执行时间：', time, '\n'
                            '是否肉鸽：', rogue, '\n'
                            '打哪个（如果打）：', rogue_name)

        # self.account_timer_thread = TimerThread(times)
        # self.account_timer_thread.timer_signal.connect(self.update_output)  # 把子线程定义过去
        # self.account_timer_thread.start()
        # self.account_timer_thread = TimerThread(times)
        self.account_timer = QTimer(self)
        self.account_timer.timeout.connect(lambda: self.execute_command(times))
        self.account_timer.start(sleeptime * 1000)

    @pyqtSlot(str)  # 子线程输出
    def update_output(self, text):
        self.output_text_edit.appendPlainText(text)

    def stop_command(self):  # 停止按钮
        global app_name
        # self.account_timer = None
        # self.rogue_timer = None
        self.save_info()
        self.setWindowTitle(app_name)
        if self.account_timer.isActive():
            self.account_timer.stop()
        if self.rogue_timer.isActive():
            self.rogue_timer.stop()
        try:
            asst.stop()
            logger.debug("MAA Core stop!")
        except:
            pass

        print('停止了所有进行的任务！')
        logger.debug("All timer stop!")

    def change_command(self):
        global theme
        if theme == 'light':
            qdarktheme.setup_theme('dark')
            theme = 'dark'
        else:
            qdarktheme.setup_theme('light')
            theme = 'light'

    def skyland_sign(self):  # 签到定时器
        global adb_path, adb_port, pre_input
        with open("info.txt", "r") as f:
            times = {}  # 创建一个空字典，用于存放时间和对应的数据
            data = json.load(f)  # 加载json格式的数据为字典对象
            i = 0
            for group in data:  # 遍历字典中的每一组数据
                i += 1
                account = group["account"]
                password = group["password"]
                times[i] = [account, password]
        current_time = time.strftime('%H:%M')
        if current_time == '04:01':  # 森空岛登录
            logger.debug("Execute skyland sign.")
            for m in times:
                try:
                    logger.debug(f"Sign account:{times.get(m)[0]}")
                    token = login_by_password(times.get(m)[0], times.get(m)[1])
                    cred = get_cred_by_token(token)
                    print(do_sign(cred))
                    logger.debug(do_sign(cred))
                except:
                    print_error("森空岛签到失败，请检查网络代理")
                    logger.error("[Sign Timer]Failed to Sign Skyland, maybe the VPN is on?")

        if current_time == '03:55':
            logger.debug("Restarting game...")
            print('临近数据更新时间，重启游戏')
            try:
                asst.stop()
                logger.debug("MAA Core stop!")
            except:
                pass
            logger.debug("Connecting simulator...")
            if sim_name == 'bluestacks':
                run_command(adb_path + ' connect ' + adb_port)
                run_command(pre_input + 'input su')
            else:
                run_command(adb_path + ' connect ' + adb_port)
            time.sleep(2)
            logger.debug("Shutting down Arknights...")
            run_command(pre_input + 'am force-stop com.hypergryph.arknights')  # 关掉!方舟
            time.sleep(2)
            logger.debug("Starting Arknights...")
            run_command(pre_input + 'monkey -p com.hypergryph.arknights -c android.intent.category.LAUNCHER 1')  # 打开!方舟
            time.sleep(2)
            run_command(adb_path + ' disconnect')
            logger.debug("Restart complete!")

    def execute_command(self, times):  # 换号定时器
        global rogue_name, pre_input, is_running
        current_time = time.strftime('%H:%M')
        for m in times:
            t1 = m
            t2 = datetime.strptime(t1, "%H:%M") + timedelta(hours=12)  # 获得12h后的时间
            t2 = t2.strftime("%H:%M")  # 将datetime对象转换回字符串
            # print(t1, t2)
            if current_time == t1 or current_time == t2:
                rogue_name = times.get(m)[3]
                self.account_timer_thread = TimerThread(
                    times.get(m)[0], times.get(m)[1], times.get(m)[2], times.get(m)[4]
                )
                self.account_timer_thread.timer_signal.connect(self.update_output)  # 把子线程定义过去
                self.account_timer_thread.signal_start_rogue.connect(self.start_rogue_timer)
                if is_running is False:
                    self.account_timer_thread.start()
                # TimerThread.run(times.get(m)[0], times.get(m)[1], times.get(m)[2], times.get(m)[4])

    # def getInputs(self):
    #     return [input_group[0].text() for input_group in self.inputs]

    def start_rogue_timer(self):
        self.rogue_timer = QTimer(self)
        self.rogue_timer.timeout.connect(lambda: self.start_rogue())
        self.rogue_timer.setInterval(5 * 60 * 1000)
        self.rogue_timer.start()

    def start_rogue(self):  # 肉鸽主函数
        global adb_path, rogue_name

        # 设置为存放 dll 文件及资源的路径
        with open(''.join([str(pathlib.Path(__file__).parent.parent), r'\MAA.Judge']), "r") as f:
            judge = f.readlines()[-1]
            print('MAA当前状态：', judge)
            f.close()
        if judge == "Stop":
            # MAAGui不在运行，开始肉鸽
            logger.debug("[Rogue Timer]Detected that MAA stop,start rogue.")
            logger.debug(f"[Rogue Timer]Rogue task:{rogue_name}")
            print('此次肉鸽任务为：', rogue_name)
            # 触控方案配置  请务必设置adbinput！！！！！！！！！！！  # 戳啦，都能用啦（ # 最新消息，minitouch有几率不能用
            if asst.set_instance_option(InstanceOptionType.touch_type, 'adb'):
                logger.debug("[Rogue Timer]Adb connection successful!")
                print('Adb连接成功！')
            else:
                logger.error("[Rogue Timer]Adb connection failed, Task stop!")
                print_error('Adb连接失败，任务终止！')
                exit()
            try:
                if self.rogue_timer.isActive() is True:
                    self.rogue_timer.stop()
                else:
                    print("肉鸽定时器异常")
            except:
                pass
            asst.connect(adb_path, '127.0.0.1:5555', 'CapWithShell')
            asst.append_task('Roguelike', {
                "theme": rogue_name,  # 肉鸽名，可选，默认 "Phantom"
                # Phantom - 傀影与猩红血钻
                # Mizuki  - 水月与深蓝之树
                # Sami  - 探索者的银凇止境
                "mode": 0,  # 模式，可选项。默认 0
                # 0 - 刷蜡烛，尽可能稳定的打更多层数
                # 1 - 刷源石锭，第一层投资完就退出
                # 2 - 【即将弃用】两者兼顾，投资过后再退出，没有投资就继续往后打
                # "starts_count": int,    # 开始探索 次数，可选，默认 INT_MAX。达到后自动停止任务
                # "investment_enabled": bool, # 是否投资源石锭，默认开
                # "investments_count": int,
                # 投资源石锭 次数，可选，默认 INT_MAX。达到后自动停止任务
                # "squad": string,        # 开局分队，可选，例如 "突击战术分队" 等，默认 "指挥分队"
                # "roles": string,        # 开局职业组，可选，例如 "先手必胜" 等，默认 "取长补短"
                # "core_char": string,    # 开局干员名，可选，仅支持单个干员中！文！名！。默认识别练度自动选择
                "use_support": True,  # 开局干员是否为助战干员，可选，默认 false
                # "use_nonfriend_support": bool,  # 是否可以是非好友助战干员，可选，默认 false，use_support为true时有效
                # "refresh_trader_with_dice": bool  # 是否用骰子刷新商店购买特殊商品，目前支持水月肉鸽的指路鳞，可选，默认 false
            })
            asst.start()
        else:
            logger.debug("[Rogue Timer]Detected that MAA is running.")
            print("如果你的MAA没有在运行的话，可以双击一下文件夹内的MaaIsOff.bat")  # 我实在是想不出有什么好的检测maa是否在运行的方法了


if __name__ == '__main__':
    from PyQt5.QtCore import QTimer, QTime

    logger.debug("[--------------------------]")
    logger.debug("[--Account Changer Start!--]")
    logger.debug(f"[--Version v{version}         --]")
    logger.debug(f"[--User Dir {str(pathlib.Path(__file__).parent)} --]")
    logger.debug("[--------------------------]")

    '''初始化MAA'''
    path = pathlib.Path(__file__).parent.parent
    logger.debug(f"Loading MAA path at {str(path)}")
    Asst.load(path=path)
    asst = Asst()
    logger.debug(f"Loading MAA succeed!")

    app = QApplication(sys.argv)
    qdarktheme.setup_theme('light')
    ss = InputDialog()
    ss.show()
    ss.redirect_print_to_widget()
    ss.change_adb_path()
    if if_debug:
        if_debug = False
        ss.deeebuuuggg()
    logger.debug("GUI Start!")
    # adb_path = get_process_path('dnplayer.exe')
    # print('当前Adb路径为：', adb_path)
    sys.exit(app.exec_())
