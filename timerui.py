from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from datetime import datetime
from threading import Thread
import time

KV = '''
<AlarmItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(72)
    padding: dp(10), dp(0)
    spacing: dp(10)
    md_bg_color: 0, 0, 0, 1

    BoxLayout:
        orientation: "vertical"
        size_hint_x: 0.8
        spacing: dp(2)

        MDLabel:
            text: root.time_12
            font_style: "H4"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1

        MDLabel:
            text: "Alarm"
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: 0.7, 0.7, 0.7, 1

    MDSwitch:
        id: switch
        active: root.enabled
        on_active: root.toggle(self.active)

BoxLayout:
    orientation: 'vertical'
    spacing: dp(10)
    padding: dp(10)
    md_bg_color: 0, 0, 0, 1

    MDLabel:
        id: time_label
        text: "00:00 AM"
        font_style: "H3"
        halign: "center"
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1

    BoxLayout:
        size_hint_y: None
        height: dp(56)
        spacing: dp(10)

        MDRaisedButton:
            id: hour_picker
            text: "07"
            on_release: app.menu_open(self, 'hour')

        MDRaisedButton:
            id: minute_picker
            text: "00"
            on_release: app.menu_open(self, 'minute')

        MDRaisedButton:
            id: ampm_picker
            text: "AM"
            on_release: app.menu_open(self, 'ampm')

        MDRaisedButton:
            text: "Add Alarm"
            on_release: app.add_alarm()

    MDLabel:
        id: status_label
        text: "No alarms set"
        halign: "center"
        theme_text_color: "Custom"
        text_color: .6, .6, .6, 1

    ScrollView:
        MDList:
            id: alarm_list
'''

class AlarmItem(BoxLayout):
    def __init__(self, alarm_data, **kwargs):
        super().__init__(**kwargs)
        self.alarm_data = alarm_data
        self.time_12 = alarm_data["time_12"]
        self.enabled = alarm_data["enabled"]

    def toggle(self, is_active):
        self.alarm_data["enabled"] = is_active

class AlarmApp(MDApp):
    def build(self):
        self.alarms = []
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        Builder.load_string(KV)
        self.root = Builder.load_string(KV)
        Clock.schedule_interval(self.update_clock, 1)
        Thread(target=self.alarm_checker, daemon=True).start()
        return self.root

    def update_clock(self, dt):
        now = datetime.now().strftime("%I:%M %p")
        self.root.ids.time_label.text = now

    def convert_to_24h(self, hour, minute, period):
        hour = int(hour)
        minute = int(minute)
        if period == 'PM' and hour != 12:
            hour += 12
        elif period == 'AM' and hour == 12:
            hour = 0
        return f"{hour:02}:{minute:02}"

    def add_alarm(self):
        hour = self.root.ids.hour_picker.text
        minute = self.root.ids.minute_picker.text
        ampm = self.root.ids.ampm_picker.text
        time_12 = f"{hour}:{minute} {ampm}"
        time_24 = self.convert_to_24h(hour, minute, ampm)
        alarm_data = {"time_12": time_12, "time_24": time_24, "enabled": True}
        self.alarms.append(alarm_data)
        item = AlarmItem(alarm_data)
        self.root.ids.alarm_list.add_widget(item)
        self.root.ids.status_label.text = f"Alarm set for {time_12}"
        self.root.ids.status_label.text_color = (0.04, 0.52, 1, 1)

    def alarm_checker(self):
        while True:
            now = datetime.now().strftime("%H:%M")
            for alarm in self.alarms:
                if alarm["enabled"] and alarm["time_24"] == now:
                    print(f"Alarm Triggered: {alarm['time_12']}")
                    sound = SoundLoader.load('sound.wav')
                    if sound:
                        sound.play()
                    alarm["enabled"] = False
            time.sleep(10)

    def menu_open(self, caller, mode):
        if mode == 'hour':
            items = [f"{i:02}" for i in range(1, 13)]
        elif mode == 'minute':
            items = [f"{i:02}" for i in range(0, 60)]
        else:
            items = ['AM', 'PM']

        menu_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.menu_callback(caller, x)
            }
            for item in items
        ]

        self.menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=4
        )
        self.menu.open()

    def menu_callback(self, caller, value):
        caller.text = value
        self.menu.dismiss()

if __name__ == "__main__":
    AlarmApp().run()
