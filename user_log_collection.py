from dotenv import load_dotenv
import os
from supabase import create_client, Client
import win32gui
import win32process
import psutil
import time
import getpass
import csv
from datetime import datetime

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)
role='Developer'

def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()  
        pid = win32process.GetWindowThreadProcessId(hwnd) 
        process = psutil.Process(pid[-1]) 
        app_name = process.name()
        return app_name
    except Exception as e:
        return None

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
            writer.writerow(["Timestamp", "Application", "User", "Duration (minutes)", "Access Count"])  

        while True:
            current_app = get_active_window()
            current_time = time.time()
            if current_app:
                if current_app != last_app:
                    if last_app is not None and start_time is not None:
                        duration_minutes = (current_time - start_time) / 60
                        duration_minutes = round(duration_minutes, 2)
                    else:
                        duration_minutes = 0 

                    start_time = current_time
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")

                    if current_app in app_access_count:
                        app_access_count[current_app] += 1
                    else:
                        app_access_count[current_app] = 1

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
            time.sleep(1) 

if __name__ == "__main__":
    log_application_usage()