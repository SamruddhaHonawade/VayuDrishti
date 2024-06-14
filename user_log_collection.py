from dotenv import load_dotenv
load_dotenv()
import os
from supabase import create_client, Client
import win32gui
import win32process
import psutil
import time
import getpass
import csv
from datetime import datetime

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()  # Get handle to the foreground window
        pid = win32process.GetWindowThreadProcessId(hwnd)  # Get PID of the process
        process = psutil.Process(pid[-1])  # Get process info
        app_name = process.name()  # Get the process name
        return app_name
    except Exception as e:
        return None

def log_application_usage():
    last_app = None
    start_time = None
    app_access_count = {}  # New dictionary to keep track of application access count

    csv_file = "application_usage_log.csv"
    user_name = getpass.getuser()  # Get the current username

    # Check if the CSV file exists to write the header only once
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

                    # Only consider the applications accessed in the last 3 hours
                    three_hours_ago = time.time() - 3 * 60 * 60
                    if start_time >= three_hours_ago:
                        writer.writerow([timestamp, current_app, user_name, duration_minutes, app_access_count[current_app]])

                        # Adding data to Supabase
                        data = supabase.table("User_Anylysis").insert(
                            {"log_time": timestamp, "Application": current_app, "User_Name": user_name, "used_for": duration_minutes, "Acess_count":app_access_count[current_app]}
                        ).execute()
                        print(timestamp, current_app, user_name, f"{duration_minutes} minutes", f"Access Count: {app_access_count[current_app]}")
                    last_app = current_app
            time.sleep(1)  # Check every second



if __name__ == "__main__":
    log_application_usage()
