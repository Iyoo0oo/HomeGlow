from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

import threading
import time
import winsound
import cv2
import imutils
import serial
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

# === Global Flags and Tracking ===
alarm_mode = False
alarm = False
alarm_counter = 0
off_timer_triggered = False
no_motion_timeout = 5
last_motion_time = time.time()
light_on_time = 0.0
light_start_time = None
energy_log = []
WATTAGE = 5.0  # Light power in watts

arduino = serial.Serial(port='COM5', baudrate=9600, timeout=1)
time.sleep(2)

def find_camera_index():
    for index in range(1, 10):
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            capture.release()
            return index
    capture = cv2.VideoCapture(0)
    if capture.isOpened():
        capture.release()
        return 0
    raise RuntimeError("No camera found!")

def offtimer():
    global off_timer_triggered, light_on_time, light_start_time
    for i in range(no_motion_timeout, 0, -1):
        if time.time() - last_motion_time < no_motion_timeout:
            return
        time.sleep(1)
    if time.time() - last_motion_time >= no_motion_timeout:
        off_timer_triggered = True
        arduino.write(b'0')
        if light_start_time:
            light_on_time += time.time() - light_start_time
            light_start_time = None

def beepBoop():
    global alarm
    for _ in range(5):
        if not alarm:
            break
        winsound.Beep(2500, 1000)
    alarm = False

def check_no_motion_timer():
    global off_timer_triggered
    if time.time() - last_motion_time >= no_motion_timeout and not off_timer_triggered:
        off_timer_triggered = True
        threading.Thread(target=offtimer).start()

def energy_logger():
    global energy_log, light_on_time, light_start_time
    while True:
        if light_start_time:
            current = light_on_time + (time.time() - light_start_time)
        else:
            current = light_on_time
        energy = (current / 3600) * WATTAGE
        timestamp = time.strftime("%H:%M:%S")
        energy_log.append((timestamp, energy))
        time.sleep(5)

def start_camera_loop():
    global alarm_mode, alarm_counter, alarm, off_timer_triggered, last_motion_time, light_start_time

    camera_index = find_camera_index()
    capture = cv2.VideoCapture(camera_index)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    _, start_frame = capture.read()
    start_frame = imutils.resize(start_frame, width=500)
    start_frame = cv2.cvtColor(start_frame, cv2.COLOR_BGR2GRAY)
    start_frame = cv2.GaussianBlur(start_frame, (21, 21), 0)

    while True:
        ret, frame = capture.read()
        if not ret:
            break

        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        if alarm_mode:
            diff = cv2.absdiff(start_frame, gray_blurred)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            if thresh.sum() > 4:
                arduino.write(b'1')
                alarm_counter += 1
                last_motion_time = time.time()
                off_timer_triggered = False
                if light_start_time is None:
                    light_start_time = time.time()
            else:
                alarm_counter = max(0, alarm_counter - 1)
                check_no_motion_timer()

            cv2.imshow("Cam", thresh)

            if alarm_counter > 20:
                if not alarm:
                    alarm = True
                    threading.Thread(target=beepBoop).start()
        else:
            cv2.imshow("Cam", frame)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

        if alarm_mode:
            start_frame = gray_blurred

    capture.release()
    cv2.destroyAllWindows()

class HomeGlow(MDApp):
    def build(self):
        screen = MDScreen()
        self.layout = MDBoxLayout(orientation='vertical', padding=20, spacing=20)

        self.label = MDLabel(
            text="Alarm mode is OFF",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#FF0000"),
            font_style="H4"
        )

        self.button = MDRectangleFlatButton(
            text="Open",
            pos_hint={"center_x": 0.5},
            on_release=self.toggle_alarm,
            md_bg_color=get_color_from_hex("#FFFFFF"),
            text_color=get_color_from_hex("#000000")
        )

        self.analytics_button = MDRectangleFlatButton(
            text="View Analytics",
            pos_hint={"center_x": 0.5},
            on_release=self.show_analytics
        )

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.button)
        self.layout.add_widget(self.analytics_button)

        screen.add_widget(self.layout)

        threading.Thread(target=start_camera_loop, daemon=True).start()
        threading.Thread(target=energy_logger, daemon=True).start()

        return screen

    def toggle_alarm(self, instance):
        global alarm_mode
        alarm_mode = not alarm_mode

        if alarm_mode:
            self.label.text = "Alarm mode is ON"
            self.label.text_color = get_color_from_hex("#4CAF50")
            self.button.text = "Off"
            self.button.md_bg_color = get_color_from_hex("#5CAF50")
            self.button.text_color = get_color_from_hex("#FFFFFF")
        else:
            self.label.text = "Alarm mode is OFF"
            self.label.text_color = get_color_from_hex("#FF0000")
            self.button.text = "Open"
            self.button.md_bg_color = get_color_from_hex("#FFFFFF")
            self.button.text_color = get_color_from_hex("#000000")

    def show_analytics(self, instance):
        if not energy_log:
            return

        times = [x[0] for x in energy_log]
        values = [x[1] for x in energy_log]

        plt.figure(figsize=(8, 4))
        plt.plot(times, values, marker='o', color='blue')
        plt.title("Energy Usage Over Time")
        plt.xlabel("Time")
        plt.ylabel("Energy (Wh)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasKivyAgg(plt.gcf())
        popup = Popup(title='Energy Analytics', content=canvas,
                      size_hint=(0.9, 0.7))
        popup.open()
        plt.clf()  # clear plot to avoid stacking

HomeGlow().run()
