# -*- coding:utf-8 -*-
import tkinter as tk
from PIL import Image
import pytesseract
import time
import requests
import os
import threading
import pyperclip
from tkinter.constants import END
from urllib import parse
import tkinter.messagebox
import pystray
from pystray import MenuItem, Menu


def quit_window(icon: pystray.Icon):
    icon.stop()
    window.destroy()


def show_window():
    window.deiconify()


def on_exit():
    window.withdraw()


menu = (MenuItem('显示', show_window, default=True), Menu.SEPARATOR, MenuItem('退出', quit_window))
image = Image.open("yzm.png")
icon = pystray.Icon("icon", image, "图标名称", menu)
window = tk.Tk()
log_list = tk.Listbox(window)
xxjl = 0


def list_in(string):
    global xxjl
    if xxjl >= 30:
        log_list.delete(END)
    else:
        xxjl = xxjl + 1
    log_list.insert(0, string + "--------" + time.strftime("%H:%M:%S"))
    window.update()


log_list.place(x=20, y=250, width=360, height=340)


class gdmec:
    # 基本参数
    base_url = r'http://172.30.1.1'
    img_url = base_url + r'/eportal/validcode?rnd=?0.2744416893799772'  # 验证码地址
    login_url = base_url + r'/eportal/InterFace.do?method=login'  # 登入地址
    config_key = ''
    yzm_key = ''
    status = 0

    # 屏幕参数
    screen_height = window.winfo_screenheight()
    screen_width = window.winfo_screenwidth()
    x = screen_width / 2
    y = screen_height / 2

    # 基本配置
    config_user = ''
    config_password = ''
    config_auto_login = ''
    save_a = tk.IntVar()
    save_b = tk.IntVar()
    xc_status = 0

    # 初始化
    def __init__(self):
        if os.path.exists('config.ini'):
            with open("config.ini", "r") as f:
                lines = []
                for line in f.readlines():
                    line = line.strip('\n')
                    lines.append(line)
            if len(lines) == 0:
                os.remove('config.ini')
                return
            self.config_user = lines[0]
            self.config_password = lines[1]
            self.config_auto_login = lines[2]
            self.save_b.set(int(lines[2]))
            if len(str(lines[2])) == 0:
                self.save_a.set(0)
            else:
                self.save_a.set(1)
            session = requests.session()
            session.get("http://172.30.1.1/")
            html_set_cookie = requests.utils.dict_from_cookiejar(session.cookies)
            send_cookie = session.cookies['JSESSIONID']
            self.header = {
                "Cookie": 'JSESSIONID=' + send_cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
            }

    # 取设备码
    def get_key(self):
        ym = requests.get(self.base_url, headers=self.header)
        ym.encoding = 'utf8'
        text = ym.text
        list_in("设备码全返回：" + text)
        text = text.replace(
            "<script>top.self.location.href='http://172.30.1.1/eportal/index.jsp?", "")
        text = text.replace("'</script>", "")
        global referer
        referer = 'http://172.30.1.1/eportal/index.jsp?' + text.replace('\r\n', '')
        list_in("设备码选取：" + text)
        text = parse.quote(text)
        list_in("设备码转码：" + text)
        text = text.replace("%0D%0A", "")
        self.config_key = text
        list_in("设备码" + text)
        return text

    # 验证码下载
    def download_img(self):
        list_in("验证码开始下载")
        if os.path.exists('yzm.png'):
            os.remove('yzm.png')
        r = requests.get(self.img_url, headers=self.header)
        if r.status_code == 200:
            img_name = "yzm.png"
            with open(img_name, 'wb') as f:
                f.write(r.content)
            list_in("验证码下载成功")
            list_in("验证码开始识别")
            time.sleep(3)
            st = pytesseract.image_to_string(Image.open('yzm.png'), config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
            filter(str.isdigit, st)
            y = int(st)
            if y <= 999:
                return self.download_img()
            self.yzm_key = st
            list_in('验证码识别成功')
            list_in(f'验证码：{str(st)}')
            return st

    # 下线操作
    def exit_login(self):
        os.system('start http://172.30.1.1/')

    # 登入操作
    cishu = 0

    def login(self):
        self.cishu = self.cishu + 1
        list_in("正在进行第" + str(self.cishu + 1) + "次登入操作")
        str_url = str(self.login_url) + '&userId=' + str(self.config_user) + '&password=' + str(self.config_password) + '&service=&queryString=' + \
                  str(self.get_key()) + '&operatorPwd=&operatorUserId=&validcode=' + \
                  str(self.download_img().replace('\n', ''))
        list_in(str_url)
        list_in('读取数据')

        try:
            pyperclip.copy(str_url)
            ym = requests.post(str_url, headers=self.header)
            ym.encoding = 'utf8'
            text = ym.text
            time.sleep(10)
            list_in(text)
            if 'success' in text:
                list_in('登入成功')
                if self.ping() == 0:
                    list_in('网络连接成功')
                    self.status = 1
                    self.xc_status = 1
                    self.cishu = 0
                    return self.autologin()
                else:
                    list_in("第" + str(self.cishu + 1) + "次网络接入失败")
            if '验证码' in text:
                list_in('验证码错误')
                return self.login()
            if '密码不能为' in text:
                list_in('密钥错误')
        except:
            list_in("第" + str(self.cishu + 1) + "次登入失败")
        self.status = 0
        if self.cishu == 10:
            list_in("登入失败，请检查账号密钥")
            return
        return self.login()

    # ping网络
    # 此处原是ping命令，但是校园网未登录也是可以ping通的，故采用get方法检测
    def ping(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
        }
        try:
            r = requests.get("http://baidu.com", headers=headers)
            return 0 if r.status_code == 200 and '百度' in r.text else 1
        except:
            return 1

    # 写出配置
    def save(self):
        self.config_auto_login = self.save_b.get()
        file_ini = open('config.ini', mode='w')
        file_ini.write(str(self.config_user) + "\n" +
                       str(self.config_password) + "\n" + str(self.config_auto_login))

    # 删除配置
    def delete(self):
        if os.path.exists('config.ini'):
            os.remove('config.ini')
        self.save_a.set(0)
        self.save_b.set(0)
        self.config_auto_login = 0

    # 保存操作
    def function_save(self):
        if self.save_a.get() == 0:
            self.delete()
        else:
            self.save()

    # 自动登入操作
    def function_auto(self):
        if self.save_a.get() == 0:
            tkinter.messagebox.showinfo('提示', '请先勾选保存密码')
            self.save_b.set(0)
        else:
            self.config_auto_login = self.save_b.get()
            self.save()
            self.autologin()

    def fun_timer(self):
        icon.run()
        while True:
            if self.xc_status == 1:
                list_in("每隔10s自动检测网络连通性")
                if self.ping() == 0:
                    list_in("处于网络状态下")
                else:
                    self.xc_status = 0
                    list_in("网络连接已断开")
                    list_in("自动重连")
                    self.login()
            time.sleep(10)

    def autologin(self):
        if self.save_b.get() == 1 and self.status == 1:
            self.xc_status = 1


gdmec = gdmec()

window.geometry(f"400x600+{str(int(gdmec.x) - 200)}+{str(int(gdmec.y) - 300)}")
window.option_add('*Font', 'Fira 10')
window.resizable(width=False, height=False)
window.title('校园网登录工具')
window.update()

label_user = tk.Label(window, text='账号：')
label_password = tk.Label(window, text='密钥：')
label_title = tk.Label(window, text='校园网工具')

entry_user = tk.Entry(window)
entry_password = tk.Entry(window)

entry_user.delete(0, "end")
entry_user.insert(0, gdmec.config_user)
entry_password.delete(0, "end")
entry_password.insert(0, gdmec.config_password)

label_title.place(x=120, y=10, width=160, height=25)
label_user.place(x=50, y=50, width=50, height=30)
label_password.place(x=50, y=100, width=50, height=30)
entry_user.place(x=120, y=50, width=200, height=30)
entry_password.place(x=120, y=100, width=200, height=30)


def info_saves():
    gdmec.config_user = entry_user.get()
    gdmec.config_password = entry_password.get()
    gdmec.function_save()


info_save = tk.Checkbutton(
    window, text='保存帐密', variable=gdmec.save_a, command=info_saves)
info_auto = tk.Checkbutton(
    window, text='自动登录', variable=gdmec.save_b, command=gdmec.function_auto)

info_save.place(x=75, y=140, width=100, height=30)
info_auto.place(x=225, y=140, width=100, height=30)


def play_login():
    list_in("网络状态检测中")
    if gdmec.ping() == 0:
        gdmec.status = 1
        list_in("处于联网状态,可点击下线")
        gdmec.exit_login()
        return
    gdmec.status = 0
    gdmec.config_user = entry_user.get()
    gdmec.config_password = entry_password.get()
    gdmec.cishu = 0
    gdmec.login()


def init():
    list_in("网络状态检测中")
    if gdmec.ping() == 0:
        gdmec.status = 1
        list_in("处于联网状态")
        return
    list_in("未处于联网状态")


# 重新定义点击关闭按钮的处理

window.protocol('WM_DELETE_WINDOW', on_exit)
login_button = tk.Button(window, text='登入', command=play_login)
t = threading.Thread(target=gdmec.fun_timer, daemon=True).start()

login_button.place(x=150, y=190, width=80, height=30)
init()
if gdmec.save_b.get() == 1:
    gdmec.autologin()
window.mainloop()
