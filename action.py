#coding=utf-8
import os
import subprocess
import tkinter as tk
from tkinter import *
from system_hotkey import SystemHotkey
import win32gui
import win32api
import win32con
import json
import winreg
import datetime
import traceback
import threading


def kill(config):
    title = config.windows_title
    hwnd = win32gui.FindWindow(None, title)
    if hwnd > 0:
        win32api.SendMessage(hwnd,win32con.WM_CLOSE,0,0)

def load_lib(config):
    libs = config.libs
    commands = {}
    for lib in libs:
        coms = os.listdir(lib)
        for comm in coms:
            if comm.endswith("lnk") or comm.endswith("exe"):
                name = comm.split(".")[0]
                commands[name] = lib + "\\" + comm
    return commands

def load_software(config):

    #需要遍历的两个注册表, 
    sub_key = [r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths', r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall']
    
    software_name = {}
    
    for i in sub_key:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, i, 0, winreg.KEY_ALL_ACCESS)
        for j in range(0, winreg.QueryInfoKey(key)[0]-1):
            try:
                key_name = winreg.EnumKey(key, j)
                key_path = i + '\\' + key_name
                each_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
                try:
                    Pos, REG_SZ = winreg.QueryValueEx(each_key, '')
                except:
                    DisplayName, REG_SZ = winreg.QueryValueEx(each_key, 'DisplayName')
                    if len(DisplayName) > 15:
                        key_name = DisplayName[0:15]
                        split = key_name.split(" ")
                        if len(split) > 2:
                            key_name = "-".join(split[0:2])
                    Pos, REG_PS = winreg.QueryValueEx(each_key, 'DisplayIcon')
                    Pos = Pos.split(",")[0]
                try:
                    name = key_name.split(".")[0]
                except:
                    name = key_name
                software_name[name] = Pos
            except WindowsError as e:
                pass
    filter(config, software_name)
    rename(config, software_name)
    return software_name

def filter(config, software):
    names = config.filters
    for name in names:
        try:
            del software[name]
        except Exception as e:
            log.err(traceback.format_exc())

def rename(config, software):
    names = config.rename
    for name in names.keys():
        try:
            software[names[name]] = software[name]
            del software[name]
        except Exception as e:
            log.err(traceback.format_exc())

def load_json(name):
    with open(name, "r", encoding="utf-8") as f:
        lines = f.read()
    return json.loads(lines)

config_info = load_json("configuration.json")

def load_scripts(config):
    scripts = load_json("orders.json")
    for script in config.script:
        loads = {name.split(".")[0]:"python "+ script + name + " $@" for name in os.listdir(script) if name.endswith(".py")}
        scripts.update(loads)
    scripts.update(load_lib(config))
    if(config.load_software):
        try:
            scripts.update(load_software(config))
        except Exception as e:
            log.err(traceback.format_exc())
    return scripts

class Config:

    def __init__(self, config):
        self.config = config
        # 程序背景颜色
        self.bg = config['background-color']
        # 程序文字颜色
        self.fg = config['font-color']
        # 关键字颜色
        self.key_fg = config['key-color']
        # 关键字字体
        self.key_font = tuple(config['key-font'])
        # 结果集字体
        self.result_font = tuple(config['result-font'])
        # 关键字最大显示字长
        self.max_key_length = config['max-key-length']
        # 关键字左间距
        self.key_left_margin = config['key-left-margin']
        # 脚本位置
        self.script = config['scripts-path']
        # 程序高度
        self.windows_height = config['windows-height']
        # 程序标题
        self.windows_title = config['windows-title']
        # 系统热键
        self.active_hotkey = tuple(config['active-hotkey'])
        # 选中高亮颜色
        self.selected_color = config['selected-color']
        # rename
        self.rename = config['rename']
        self.selected_bg = config['selected-background-color']
        self.load_software = config['load-software']
        self.filters = config['filters']
        self.libs = config['lib-path']
        self.notification = config['notification']
        self.hover_input = config['hover-input']


class Bar:

    def __init__(self, config, orders):
        self.config = config
        self.win = tk.Tk()
        # 系统热键
        self.hk = SystemHotkey()

        self.screen_width = self.win.winfo_screenwidth()
        self.win.geometry(str(self.screen_width)+"x"+str(config.windows_height))
        self.win['background'] = config.bg
        self.win.title(config.windows_title)
        self.win.overrideredirect(True)
        self.history = History(config)

        # 关键字gui
        self.key = StringVar()
        # 关键字
        self.order = ""
        # 所有命令
        self.orders = orders
        # 结果集的label gui
        self.result_labels = {}
        # 当前被选中的结果下标
        self.selected_index = -1 
        # 当前被选中的结果
        self.selected_label = None
        self.last_index = 0

        # 表示关键字的label
        self.key_label = Label(self.win, anchor='w',textvariable=self.key, bd=config.key_left_margin, fg=config.key_fg, bg=config.bg, width=config.max_key_length, font=config.key_font)
        # 结果集的容器
        self.result_frame = Frame(self.win, bg=config.bg)
        # 注册系统热键
        self.hk.register(config.active_hotkey, callback=self.show)

        self.key_label.focus_set()
        self.key_label.pack(side='left')
        self.key_label.bind("<Key>", self.deal)
        self.key_label.bind("<Return>", self.key_action)
        self.key_label.bind("<BackSpace>", self.delete)
        self.key_label.bind("<Escape>", self.hide)
        self.key_label.bind("<Tab>", self.next)
        self.key_label.bind("<Control-v>", self.paste_action)
        self.key_label.bind("<KeyPress-Right>", self.next)
        self.key_label.bind("<KeyPress-Down>", self.next_order)
        self.key_label.bind("<KeyPress-Left>", self.preview)
        self.key_label.bind("<KeyPress-Up>", self.pre_order)
        self.key_label.bind("<Control-u>", self.clear)
        self.result_frame.pack(side='left')
        self.win.update()
        self.result_frame_width = self.screen_width-self.result_frame.winfo_x()
        self.result_frame.configure(width=self.result_frame_width)
        self.win.update()

        self.update()
        self.win.mainloop()

    def next_order(self, event):
        next = self.history.get_next()
        self._update_order(next)

    
    def pre_order(self, event):
        pre = self.history.get_preview()
        self._update_order(pre)

    def clear(self, event):
        self._update_order("")
        self.update()

    def preview(self, event):
        self.selected_index -= 1
        if(self.selected_index < 0):
            self.show_preview_page()
            self.selected_index = len(self.result_labels) - 1
        try:
            self.order = self.result[self.selected_index+self.last_index-len(self.result_labels)]
            self.selected(self.order)
            self._update_order(self.order)
        except Exception as e:
            log.err(traceback.format_exc())

    def next(self, event):
        self.selected_index += 1
        if(self.selected_index > len(self.result_labels)-1):
            self.selected_index = 0
            self.show_next_page()
        try:
            self.order = self.result[self.selected_index+self.last_index-len(self.result_labels)]
            self.selected(self.order)
            self._update_order(self.order)
        except Exception as e:
            log.err(traceback.format_exc())

    def delete(self, event):
        self.order = self.order[:-1]
        if(len(self.order) > self.config.max_key_length):
            self.key.set(self.order[-self.config.max_key_length:])
        else:
            self.key.set(self.order)
        self.update()

    def deal(self, event):
        self.order += event.char
        self._update_order(self.order)
        self.selected_index = -1 
        self.update()
        self.history.flush()

    def mouse_action(self, event):
        widget = event.widget
        name = widget['text']
        self.action(name)
    
    def mouse_copy(self, event):
        widget = event.widget
        name = widget['text']
        self.win.clipboard_clear()
        self.win.clipboard_append(name)
        self.win.update()
    
    def paste_action(self, event):
        paste = self.win.clipboard_get()
        self._update_order(paste)
        self.update()

    def mouse_hover(self, event):
        widget = event.widget
        name = widget['text']
        if self.config.hover_input:
            self._update_order(name)
        self.selected(name)

    def key_action(self, event):
        splits = self.order.split(" ")
        if(len(splits) > 1):
            name = splits[0]
            self.action(name, splits[1:])
        else:
            name = self.order
            self.action(name)
    
    def thread_action(self, name, avgs=[], flag=False):
        try:
            act = self.orders[name]
            self.history.append(name+" "+" ".join(avgs))
            if "exit" == act:
                self.win.destroy()
            else:
                ord = act.replace("$@", " ".join(avgs))
        except:
            if not flag:
                self.thread_action(name+" "+" ".join(avgs), flag= True)
                return None
            else:
                ord = self.order
                self.history.append(ord)

        ord = ord.replace('"',"")
        ord = ord.split(" ")
        back = subprocess.call(ord, shell=True)
        msg = back
        # msg = "".join([s.decode('utf-8','ignore') for s in msg])
        title = " ".join(ord)
        log.info(title+"\n"+str(msg))
        # if len(msg) > 0 and self.config.notification:
        #     toaster = ToastNotifier()
        #     toaster.show_toast(title,msg,
        #             icon_path="icon.ico",
        #             duration=5,
        #             threaded=True)


    def action(self, name, avgs=[], flag=False):
        print("in")
        threading.Thread(target=self.thread_action,args=(name,avgs,flag)).start()
        self.hide()
        print("out")

    def hide(self, event=None):
        self.selected_index = 0
        self.win.withdraw()  
    
    def show(self, event):
        self.win.deiconify() 
        w1hd = win32gui.FindWindow(0, config.windows_title)
        w2hd=win32gui.FindWindowEx(w1hd,None,None,None)
        win32gui.SetForegroundWindow(w2hd)
        self._update_order("")
        self.update()
        self.history.flush()
    
    def _update_order(self, order):
        self.order = order
        if(len(self.order) > self.config.max_key_length):
            self.key.set(self.order[-self.config.max_key_length:])
        else:
            self.key.set(self.order)
    
    def update(self):
        name = self.order.split(" ")[0].lower()
        self.result = []
        for ord in self.orders:
            if name in ord.lower():
                self.result.append(ord)
        self.result.sort(key=len)
        self.last_index = 0
        self.show_next_page()
    
    def show_preview_page(self):
        self.last_index = self.last_index - len(self.result_labels)
        self.result_labels = {}
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        shows = self.result[:self.last_index]
        shows.reverse()
        length = 0
        for title in shows:
            label = Label(self.result_frame, text=title, fg=self.config.fg, bg=self.config.bg, font=self.config.result_font, padx = 5)
            label.bind('<Button-1>', self.mouse_action)
            label.bind('<Button-3>', self.mouse_copy)
            label.bind('<Enter>', self.mouse_hover)
            label.pack(side=RIGHT)
            self.win.update()
            try:
                length += label.winfo_width()
            except Exception as e:
                log.err(traceback.format_exc())
            if length > self.result_frame_width:
                label.destroy()
                break
            else:
                self.result_labels[title] = label

    def show_next_page(self):
        self.result_labels = {}
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        if len(self.result) > 0:
            length = 0
            shows = self.result[self.last_index:]
            for i in range(len(shows)):
                tit = shows[i]
                label = Label(self.result_frame, text=tit, fg=self.config.fg, bg=self.config.bg, font=self.config.result_font, padx = 5)
                label.bind('<Button-1>', self.mouse_action)
                label.bind('<Button-3>', self.mouse_copy)
                label.bind('<Enter>', self.mouse_hover)
                label.pack(side='left')
                self.win.update()
                try:
                    print(length)
                    length += label.winfo_width()
                except Exception as e:
                    log.err(traceback.format_exc())
                if length > self.result_frame_width:
                    label.destroy()
                    break
                else:
                    self.result_labels[tit] = label
                    self.last_index += 1


    def selected(self, name):
        try:
            self.selected_label.configure(fg=self.config.fg, bg=self.config.bg)
        except Exception as e:
            pass
        self.selected_label = self.result_labels[name]
        self.result_labels[name].configure(fg=self.config.selected_color, bg=self.config.selected_bg)

class Log:

    def __init__(self, config=None):
        self.file = "action.log"
        if not os.path.exists(self.file):
            with open(self.file, 'w') as f:
                pass
        self.model = "{}:[{}]--: {}"


    def append(self, msg):
        with open(self.file, 'a') as f:
            f.write(msg+'\n')
    
    def debug(self, msg):
        msg = self.model.format("Debug",datetime.datetime.now(), msg)
        self.append(msg)

    def info(self, msg):
        msg = self.model.format("Info",datetime.datetime.now(), msg)
        msg = "Info:[{}]--: {}".format(datetime.datetime.now(), msg)
        self.append(msg)

    def err(self, msg):
        msg = self.model.format("Error",datetime.datetime.now(), msg)
        self.append(msg)


class History:

    def __init__(self, config=None):
        self.config = config
        self.file = 'history.txt'
        if not os.path.exists(self.file):
            with open(self.file, 'w') as f:
                pass
        self.buf_length = 20 
        self.init()

    def init(self):
        with open(self.file, 'r') as f:
            his = f.readlines()
            self.length = len(his)

            if self.length > self.buf_length:
                self.file_cursor = self.length - self.buf_length
                self.buffer = his[self.file_cursor:]
                self.has_next = True
                self.buf_cursor = self.buf_length
            else:
                self.buffer = his
                self.buf_cursor = self.length
                self.file_cursor = 0
                self.has_next = False 

    def append(self, order):
        self.buffer.append(order)
        self.length += 1
        self.has_next = True
        with open(self.file, 'a') as f:
            f.write(order+'\n')

    def update_buf(self):
        if self.has_next:
            with open(self.file, 'r') as f:
                his = f.readlines()

                if self.file_cursor > self.buf_length:
                    self.buffer = his[self.file_cursor-self.buf_length:self.file_cursor] + self.buffer
                    self.file_cursor = self.file_cursor-self.buf_length
                    self.has_next = True
                    self.buf_cursor = self.buf_length - 1
                else:
                    reads = his[:self.file_cursor]
                    self.buffer = reads + self.buffer
                    self.file_cursor = 0
                    self.has_next = False 
                    self.buf_cursor = len(reads) - 1
        else:
            self.buf_cursor = 0 
    
    def flush(self):
        self.buf_cursor = len(self.buffer)

    def get_next(self):
        self.buf_cursor += 1
        if self.buf_cursor < len(self.buffer):
            return self.buffer[self.buf_cursor].strip()
        else:
            self.buf_cursor = len(self.buffer)
            return ""
    
    def get_preview(self):
        self.buf_cursor -= 1
        if self.buf_cursor < 0:
            self.update_buf()
        try:
            return self.buffer[self.buf_cursor].strip()
        except:
            return ""
        
    

config = Config(config_info)
log = Log(config)
kill(config)
bar = Bar(config, load_scripts(config))