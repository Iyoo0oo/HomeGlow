from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivy.utils import get_color_from_hex
import threading
import time
import winsound
import cv2
import imutils

# === Global Flags ===
alarm_mode = False
alarm = False
alarm_counter = 0
off_timer_triggered = False
no_motion_timeout = 5
last_motion_time = time.time()

def find_camera_index():
    for index in range(1, 10):
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            capture.release()
            print(f"External camera found at index {index}")
            return index
    capture = cv2.VideoCapture(0)
    if capture.isOpened():
        capture.release()
        print("Internal camera found at index 0")
        return 0
    raise RuntimeError("No camera found!")

def offtimer():
    global off_timer_triggered
    print("⏳ Off-timer started. System will turn off if no motion continues.")
    for i in range(no_motion_timeout, 0, -1):
        if time.time() - last_motion_time < no_motion_timeout:
            print("❌ Motion detected during countdown. Timer cancelled.")
            return
        print(f"Turning off in {i}...")
        time.sleep(1)
    if time.time() - last_motion_time >= no_motion_timeout:
        print("⏲️ No motion detected for 5 seconds. Turning off...")
        off_timer_triggered = True

def beepBoop():
    global alarm
    for _ in range(5):
        if not alarm:
            break
        print("🔔 Movement detected!")
        winsound.Beep(2500, 1000)
    alarm = False

def check_no_motion_timer():
    global off_timer_triggered
    no_motion_duration = time.time() - last_motion_time
    if no_motion_duration >= no_motion_timeout and not off_timer_triggered:
        print(f"🕒 No motion for {int(no_motion_duration)} seconds. Starting off-timer.")
        off_timer_triggered = True
        threading.Thread(target=offtimer).start()

def start_camera_loop():
    global alarm_mode, alarm_counter, alarm, off_timer_triggered, last_motion_time

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
            print("Failed to read from camera. Exiting...")
            break

        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        if alarm_mode:
            difference = cv2.absdiff(start_frame, gray_blurred)
            threshold = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations=2)

            if threshold.sum() > 4:
                print("Motion detected")
                alarm_counter += 1
                last_motion_time = time.time()
                off_timer_triggered = False
            else:
                alarm_counter = max(0, alarm_counter - 1)
                check_no_motion_timer()

            cv2.imshow("Cam", threshold)

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
        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=20)

        self.label = MDLabel(
            text="Alarm mode is OFF",  # Initial state
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#FF0000"),  # RED when off
            font_style="H4"
        )

        self.button = MDRectangleFlatButton(
            text="Open",  # Initial button text for OFF state
            pos_hint={"center_x": 0.5},
            on_release=self.toggle_alarm,
            md_bg_color=get_color_from_hex("#FFFFFF"),  # White background
            text_color=get_color_from_hex("#000000")    # Black text
        )

        layout.add_widget(self.label)
        layout.add_widget(self.button)
        screen.add_widget(layout)

        threading.Thread(target=start_camera_loop, daemon=True).start()
        return screen

    def toggle_alarm(self, instance):
        global alarm_mode
        alarm_mode = not alarm_mode

        if alarm_mode:
            self.label.text = "Alarm mode is ON"
            self.label.text_color = get_color_from_hex("#4CAF50")  # Green text
            self.button.text = "Off"
            self.button.md_bg_color = get_color_from_hex("#5CAF50")  # Green
            self.button.text_color = get_color_from_hex("#FFFFFF")   # White
        else:
            self.label.text = "Alarm mode is OFF"
            self.label.text_color = get_color_from_hex("#FF0000")  # Red text
            self.button.text = "Open"
            self.button.md_bg_color = get_color_from_hex("#FFFFFF")  # White
            self.button.text_color = get_color_from_hex("#000000")   # Black

        print("Alarm mode toggled:", "ON" if alarm_mode else "OFF")

HomeGlow().run()



#andrew made oollaattt