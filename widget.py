import os
import tkinter as tk
from tkinter import *
from system_hotkey import SystemHotkey
import win32gui
import json

def load_json(name):
    with open(name, "r", encoding="utf-8") as f:
        lines = f.read()
    return json.loads(lines)

config_info = load_json("configuration.json")

def load_scripts(config):
    scripts = load_json("orders.json")
    loads = {name.split(".")[0]:"python "+ config.script + name + " $@" for name in os.listdir(config.script) if name.endswith(".py")}
    scripts.update(loads)
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

        screen_width = self.win.winfo_screenwidth()
        self.win.geometry(str(screen_width)+"x"+str(config.windows_height))
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
        self.selected_index = 0
        # 当前被选中的结果
        self.selected_label = None

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
        self.result_frame.pack(side='left')

        self.update()
        self.win.mainloop()

    def next(self, event):
        if(len(self.result) > 0):
            self.order = self.result[self.selected_index]
            self.selected(self.order)
            self._update_order(self.order)
        if(self.selected_index >= len(self.result)-1):
            self.selected_index = 0
        else:
            self.selected_index += 1


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
        self.selected_index = 0
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
            os.system(ord)
        except:
            os.system(self.order)
        self.hide()

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
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        name = self.order.split(" ")[0]
        self.resule_labels = {}
        self.result = []
        for ord in self.orders:
            if name in ord.lower():
                self.result.append(ord)
        self.result.sort(key=len)
        for title in self.result:
            label = Label(self.result_frame, text=title, fg=self.config.fg, bg=self.config.bg, font=self.config.result_font, padx = 5)
            label.bind('<Button-1>', self.mouse_action)
            label.bind('<Enter>', self.mouse_hover)
            label.pack(side='left')
            self.result_labels[title] = label

    def selected(self, name):
        try:
            self.selected_label.configure(fg=self.config.fg)
        except:
            pass
        self.selected_label = self.result_labels[name]
        self.result_labels[name].configure(fg=self.config.selected_color)


config = Config(config_info)
bar = Bar(config, load_scripts(config)) 