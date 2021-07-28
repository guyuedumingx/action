import os
import tkinter as tk
from tkinter import *
from system_hotkey import SystemHotkey
import win32gui
import json
import socket
import winreg


def load_software():

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
            except WindowsError:
                pass
    return software_name

def load_json(name):
    with open(name, "r", encoding="utf-8") as f:
        lines = f.read()
    return json.loads(lines)

config_info = load_json("configuration.json")

def load_scripts(config):
    scripts = load_json("orders.json")
    loads = {name.split(".")[0]:"python "+ config.script + name + " $@" for name in os.listdir(config.script) if name.endswith(".py")}
    scripts.update(loads)
    scripts.update(load_software())
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
        self.key_label.bind("<KeyPress-Right>", self.next)
        self.key_label.bind("<KeyPress-Down>", self.next)
        self.key_label.bind("<KeyPress-Left>", self.preview)
        self.key_label.bind("<KeyPress-Up>", self.preview)
        self.key_label.bind("<Control-u>", self.clear)
        self.result_frame.pack(side='left')
        self.win.update()
        self.result_frame_width = self.screen_width-self.result_frame.winfo_x()
        self.result_frame.configure(width=self.result_frame_width)
        self.win.update()

        self.update()
        self.win.mainloop()

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
        except:
            pass

    def next(self, event):
        self.selected_index += 1
        if(self.selected_index > len(self.result_labels)-1):
            self.selected_index = 0
            self.show_next_page()
        try:
            self.order = self.result[self.selected_index+self.last_index-len(self.result_labels)]
            self.selected(self.order)
            self._update_order(self.order)
        except:
            pass

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

    def mouse_action(self, event):
        widget = event.widget
        name = widget['text']
        self.action(name)

    def mouse_hover(self, event):
        widget = event.widget
        name = widget['text']
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

    def action(self, name, avgs=[]):
        try:
            act = self.orders[name]
            ord = act.replace("$@", " ".join(avgs))
            ord = self.chdir(ord)
            os.system(ord)
        except:
            os.system(self.order)
        self.hide()

    def chdir(self, action):
        split = action.split("\\") 
        sub_paths = split[1:-1]
        flag = False
        if len(sub_paths) > 0:
            for path in sub_paths:
                if " " in path:
                    flag = True
                    break
            if not flag:
                return action
            else:
                heads = split[0].split(" ")
                head = heads[-1]
                os.chdir(head) 
                for path in sub_paths:
                    os.chdir(path) 
                tail = split[-1]
                return " ".join(heads[:-1]) + " " + tail
        else:
            return action


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
            label.bind('<Enter>', self.mouse_hover)
            label.pack(side=RIGHT)
            self.win.update()
            print(label.winfo_width())
            length += label.winfo_width()
            if length > self.result_frame_width:
                label.destroy()
                break
            else:
                self.result_labels[title] = label

    def show_next_page(self):
        self.result_labels = {}
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        length = 0
        for title in self.result[self.last_index:]:
            label = Label(self.result_frame, text=title, fg=self.config.fg, bg=self.config.bg, font=self.config.result_font, padx = 5)
            label.bind('<Button-1>', self.mouse_action)
            label.bind('<Enter>', self.mouse_hover)
            label.pack(side='left')
            self.win.update()
            length += label.winfo_width()
            if length > self.result_frame_width:
                label.destroy()
                break
            # x = label.winfo_x()
            # if len(self.result_labels)>0 and x == 0:
            #     label.destroy()
            #     break
            else:
                self.result_labels[title] = label
                self.last_index += 1


    def selected(self, name):
        try:
            self.selected_label.configure(fg=self.config.fg)
        except:
            pass
        self.selected_label = self.result_labels[name]
        self.result_labels[name].configure(fg=self.config.selected_color)


config = Config(config_info)
bar = Bar(config, load_scripts(config)) 