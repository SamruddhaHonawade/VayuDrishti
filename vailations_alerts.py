from datetime import datetime
import os
from supabase import create_client, Client
import win32gui
from dotenv import load_dotenv
import win32process
import psutil
import time
import getpass
import csv
import cv2
import threading
import random
load_dotenv()


url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")


supabase = create_client(url, key)
#role='Developer'
role='Marketing'


role_app_access = {
    "Developer": ["pycharm64.exe", "python.exe", "code.exe", "sublime_text.exe", "idea64.exe", "eclipse.exe","ApplicationFrameHost.exe"],
    "Designer": ["photoshop.exe", "illustrator.exe", "sketch.exe", "figma.exe"],
    "Finance": ["excel.exe", "sheets.exe", "quickbooks.exe"],
    "Marketing": ["photoshop.exe", "illustrator.exe", "figma.exe", "chrome.exe","explorer.exe"],
}


app_access_limit = {
    "pycharm64.exe": 20,
    "code.exe": 20,
    "sublime_text.exe": 10,
    "idea64.exe": 10,
    "ApplicationFrameHost.exe":5,
    "eclipse.exe": 10,
    "settings.exe": 5,
    "SearchHost.exe": 3,
    "RuntimeBroker.exe": 3,
    "MicrosoftEdge.exe": 5,
    "chrome.exe": 5,
    "Notepad.exe":2,



}


violations = {}
user_name = getpass.getuser()

def capture_photo():

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True:

            ret, frame = cap.read()
            cv2.imshow("Press 's' to save or 'q' to quit", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):  # Press 's' to save the photo
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"captured_photo_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Photo saved as {filename}")

            elif key == ord('q'):
                break

            time.sleep(1)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        bucket_name: str = "Samruddha"
        new_file = filename
        r_num = random.randint(1, 10)
        fileimg_name = "user1" + str(r_num) + ".png"
        data = supabase.storage.from_(bucket_name).upload(fileimg_name, new_file)
        print(data)

def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid[-1])
        app_name = process.name()
        return app_name
    except Exception as e:
        return None


def log_violations(app, duration):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")
    count = violations[app]
    supabase.table("violations").insert(
        {"user_name": user_name, "application": app, "violation_count": count, "timestamp": timestamp, "role": role, "duration": duration}
    ).execute()


def log_application_usage():
    last_app = None
    app_access_count = {}
    start_time = None
    no_action_start_time = None

    csv_file = "application_usage_log.csv"
    user_name = getpass.getuser()


    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Application", "User", "Duration (minutes)", "Access Count"])  # Updated header

        while True:
            current_app = get_active_window()
            current_time = time.time()
            if current_app:
                if current_app != last_app:
                    if last_app is not None and start_time is not None:
                        # Calculate the duration the last app was active
                        duration_minutes = (current_time - start_time) / 60
                        duration_minutes = round(duration_minutes, 2)
                    else:
                        duration_minutes = 0  # Initial application or very short duration

                    # Update the start time for the new application
                    start_time = current_time
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")  # Format timestamp

                    # Update the access count for the current application
                    if current_app in app_access_count:
                        app_access_count[current_app] += 1
                    else:
                        app_access_count[current_app] = 1


                    print(f"Debug: {current_app} - Access Count: {app_access_count[current_app]}, Access Limit: {app_access_limit.get(current_app, 'No limit set')}")


                    if current_app in app_access_limit and app_access_count[current_app] > app_access_limit[current_app]:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time
                        # code to Db

                        supabase.table("Alerts").insert(
                            {"alert": f'The application {current_app} has been accessed more than {app_access_limit[current_app]} Times used by {user_name}', "user_name":user_name}
                        ).execute()
                        capture_photo()
                        print(f"Alert: The application {current_app} has been accessed more than {app_access_limit[current_app]} times at {current_time}!")


                    user_role = supabase.table("user_analysis").select("role").filter("user_name", "eq", user_name).execute().data[0]["role"]
                    if user_role not in role_app_access or current_app not in role_app_access[user_role]:

                        if current_app in violations:
                            violations[current_app] += 1
                        else:
                            violations[current_app] = 1
                        print(f"Violation: {user_name} accessed {current_app} which is not allowed for their role {user_role}. Total violations for this app: {violations[current_app]}")
                        log_violations(current_app, duration_minutes)

                    three_hours_ago = time.time() - 3 * 60 * 60
                    if start_time >= three_hours_ago:
                        writer.writerow([timestamp, current_app, user_name, duration_minutes, app_access_count[current_app]])

                        supabase.table("user_analysis").insert(
                            {"log_time": timestamp, "application": current_app, "user_name": user_name, "duration": duration_minutes, "access_count": app_access_count[current_app],"role":role}
                        ).execute()
                        print(timestamp, current_app, user_name, f"{duration_minutes} minutes", f"Access Count: {app_access_count[current_app]}")
                    last_app = current_app
                    no_action_start_time = None
            else:

                if no_action_start_time is None:
                    no_action_start_time = current_time
                else:

                    if current_time - no_action_start_time >= 60:
                        print("Alert: No process has been in action for 1 minute!")
            time.sleep(1)  # Check every second

if __name__ == "__main__":
    log_application_usage()
