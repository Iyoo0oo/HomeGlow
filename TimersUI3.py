import tkinter as tk
from tkinter import ttk
import datetime
import time
import winsound
from threading import Thread

root = tk.Tk()
root.title("iPhone-style Alarm")
root.geometry("360x640")
root.configure(bg="black")

font_main = ("Helvetica Neue", 24)
font_small = ("Helvetica Neue", 14)
text_color = "#FFFFFF"
accent_color = "#0A84FF"

alarms = []

hour_var = tk.StringVar(value='07')
minute_var = tk.StringVar(value='00')
ampm_var = tk.StringVar(value='AM')

status_label = None

def update_clock():
    now = datetime.datetime.now().strftime("%I:%M %p")
    time_label.config(text=now)
    root.after(1000, update_clock)

def alarm_checker():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for alarm in alarms:
            if alarm['enabled']:
                alarm_time = alarm['time']
                if now == alarm_time:
                    print(f"Alarm Triggered: {alarm_time}")
                    winsound.PlaySound("sound.wav", winsound.SND_ASYNC)
                    alarm['enabled'] = False
        time.sleep(10)

def convert_to_24h(hour, minute, period):
    hour = int(hour)
    minute = int(minute)
    if period == 'PM' and hour != 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    return f"{hour:02}:{minute:02}"

def create_alarm_item(container, time_str_12, time_str_24, is_on):
    frame = tk.Frame(container, bg='black')
    frame.pack(fill='x', pady=5, padx=20)

    time_frame = tk.Frame(frame, bg='black')
    time_frame.pack(side='left')

    time_main, time_period = time_str_12.split(" ")

    time_label = tk.Label(time_frame, text=time_main, font=('Helvetica', 36), fg='white', bg='black')
    time_label.pack(side='left')

    am_pm_label = tk.Label(time_frame, text=time_period, font=('Helvetica', 18), fg='white', bg='black', padx=4)
    am_pm_label.pack(side='left', anchor='s')

    alarm_label = tk.Label(frame, text="Alarm", font=('Helvetica', 12), fg='gray', bg='black')
    alarm_label.pack(anchor='w')

    def toggle():
        alarm['enabled'] = not alarm['enabled']

    switch = ttk.Checkbutton(frame, style='Switch.TCheckbutton', command=toggle)
    switch.pack(side='right')
    if is_on:
        switch.state(['selected'])

    alarm = {'time': time_str_24, 'enabled': is_on}
    alarms.append(alarm)

def add_alarm():
    hour = hour_var.get()
    minute = minute_var.get()
    period = ampm_var.get()
    time_24 = convert_to_24h(hour, minute, period)
    time_12 = f"{hour}:{minute} {period}"
    create_alarm_item(alarm_list_frame, time_12, time_24, True)
    status_label.config(text=f"Alarm set for {time_12}", fg=accent_color)

style = ttk.Style()
style.theme_use('default')

style.configure('TCombobox',
    fieldbackground="#1C1C1E",
    background="#1C1C1E",
    foreground=text_color,
    borderwidth=0
)

style.map("TCombobox",
    fieldbackground=[("readonly", "#1C1C1E")],
    background=[("readonly", "#1C1C1E")],
    foreground=[("readonly", text_color)]
)

style.configure("Switch.TCheckbutton",
    background='black',
    foreground=text_color,
    font=font_small
)

time_label = tk.Label(root, text="", font=("Helvetica Neue", 40, "bold"), fg=text_color, bg="black")
time_label.pack(pady=20)
update_clock()

picker_frame = tk.Frame(root, bg="black")
picker_frame.pack(pady=10)

hours = [f"{i:02}" for i in range(1, 13)]
minutes = [f"{i:02}" for i in range(0, 60)]

hour_menu = ttk.Combobox(picker_frame, values=hours, textvariable=hour_var, font=font_small, width=5, justify="center")
hour_menu.pack(side="left", padx=5)

minute_menu = ttk.Combobox(picker_frame, values=minutes, textvariable=minute_var, font=font_small, width=5, justify="center")
minute_menu.pack(side="left", padx=5)

ampm_menu = ttk.Combobox(picker_frame, values=["AM", "PM"], textvariable=ampm_var, font=font_small, width=5, justify="center")
ampm_menu.pack(side="left", padx=5)

add_btn = ttk.Button(root, text="Add Alarm", command=add_alarm)
add_btn.pack(pady=10)

status_label = tk.Label(root, text="No alarms set", font=font_small, fg="gray", bg="black")
status_label.pack(pady=5)

alarm_list_frame = tk.Frame(root, bg='black')
alarm_list_frame.pack(fill='both', expand=True, pady=10)

Thread(target=alarm_checker, daemon=True).start()

root.mainloop()
# gawa ni cla
#jashdf