import os
from sys import argv
import tkinter as tk
from tkinter import *
from system_hotkey import SystemHotkey
from win32gui import *
import win32gui
import json


def load_config(name):
    with open(name, "r", encoding="utf-8") as f:
        lines = f.read()
    return json.loads(lines)

win = tk.Tk()
config = load_config("configuration.json")

bg = config['background-color']
fg = config['font-color']
key_fg = config['key-color']
key_font=tuple(config['key-font'])
result_font=tuple(config['result-font'])
screen_width = win.winfo_screenwidth()
win.geometry(str(screen_width)+"x"+str(config['windows-height']))

win['background'] = bg
win.title(config['windows-title'])
win.overrideredirect(True)

key = StringVar()
max_key_length = config['max-key-length']
script = config['scripts-path']
order = ""
orders = [name.split(".")[0] for name in os.listdir(script)]
show = []
show_labels = []
selected_index = 0

key_label = tk.Label(win, anchor='w',textvariable=key, bd=config['key-left-margin'],fg=key_fg, bg=bg, width=max_key_length, font=key_font)
result_frame = Frame(win, bg=bg)

def deal(event):
    global order 
    global selected_index
    order += event.char
    selected_index = 0
    if(len(order) > max_key_length):
        key.set(order[-max_key_length:])
    else:
        key.set(order)
    update()

def delete(event):
    global order
    order = order[:-1]
    if(len(order) > max_key_length):
        key.set(order[-max_key_length:])
    else:
        key.set(order)
    update()

def next(event):
    global order
    global selected_index

    if(len(show) > 0):
        order = show[selected_index]
    if(len(order) > max_key_length):
        key.set(order[-max_key_length:])
    else:
        key.set(order)
    if(selected_index >= len(show)):
        selected_index = 0
    else:
        selected_index += 1
    update()


def esc(event):
    # win.destroy()
    key.set(order)
    win.withdraw()  # 实现主窗口隐藏

def action(event):
    splits = order.split(" ")
    if(len(splits) > 1):
        name = show[0]
        do(name, splits[1:])
    else:
        try:
            name = show[0]
        except:
            name = order
        do(name)

def key_action(event):
    widget = event.widget
    name = widget['text']
    do(name)

def do(name, avgs=[]):
    if name in orders:
        try:
            with open(script+name+"."+config['scripts-suffix'], "r") as f:
                lines = f.readlines()
            for line in lines:
                os.system(line)
        except:
            os.system("python " + script+name+".py" + " " + " ".join(avgs))

    else:
        os.system(order)
    # win.destroy()
    win.withdraw()  # 实现主窗口隐藏

def update():
    global result_frame
    for widget in result_frame.winfo_children():
        widget.destroy()
    name = order.split(" ")[0]
    global show
    global show_labels
    show_labels = []
    show = []
    for ord in orders:
        if(name in ord):
            show.append(ord)
    for title in show:
        label = Label(result_frame, text=title, fg=fg, bg=bg, font=result_font, padx = 5)
        label.bind('<Button-1>', key_action)  # 鼠标左键按下
        label.pack(side='left')
        show_labels.append(label)
    try:
        show_labels[0].configure(fg=config['selected-color'])
    except:
        pass

def show_win(event):
    win.deiconify()  # 显示隐藏的窗口
    w1hd = win32gui.FindWindow(0, config['windows-title'])
    w2hd=win32gui.FindWindowEx(w1hd,None,None,None)
    win32gui.SetForegroundWindow(w2hd)
    global order 
    order = ""
    key.set(order)
    update()


hk = SystemHotkey()
hk.register(tuple(config['active-hotkey']), callback=show_win)

key_label.focus_set()
key_label.pack(side='left')
key_label.bind("<Key>", deal)
key_label.bind("<Return>", action)
key_label.bind("<BackSpace>", delete)
key_label.bind("<Escape>", esc)
key_label.bind("<Tab>", next)
# separator = Separator(win, orient='vertical')
# separator.pack(fill='y')
# separator.pack(side='left')
result_frame.pack(side='left')
for ord in orders:
    label = tk.Label(result_frame, text=ord, fg=fg, bg=bg, font=result_font, padx = 5)
    label.bind('<Button-1>', key_action)  # 鼠标左键按下
    label.pack(side='left')
win.mainloop()

