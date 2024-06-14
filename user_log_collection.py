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

# Load environment variables from .env file
load_dotenv()

# Retrieve Supabase URL and Key from environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Create a Supabase client
supabase = create_client(url, key)
role='Developer'

# Function to get the active window's application name
def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()  # Get handle to the foreground window
        pid = win32process.GetWindowThreadProcessId(hwnd)  # Get PID of the process
        process = psutil.Process(pid[-1])  # Get process info
        app_name = process.name()  # Get the process name
        return app_name
    except Exception as e:
        return None

# Function to log application usage
def log_application_usage():
    last_app = None
    app_access_count = {}  # Dictionary to keep track of application access count
    start_time = None
    no_action_start_time = None  # Variable to keep track of the start time of no action

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
                        supabase.table("user_analysis").insert(
                            {"log_time": timestamp, "application": current_app, "user_name": user_name, "duration": duration_minutes, "access_count": app_access_count[current_app],"role":role}
                        ).execute()
                        print(timestamp, current_app, user_name, f"{duration_minutes} minutes", f"Access Count: {app_access_count[current_app]}")
                    last_app = current_app
                    no_action_start_time = None  # Reset the no action start time when an application is active
            else:
                # If no application is active, start the no action timer
                if no_action_start_time is None:
                    no_action_start_time = current_time
                else:
                    # If no application has been active for 1 minute, print an alert
                    if current_time - no_action_start_time >= 60:
                        print("Alert: No process has been in action for 1 minute!")
            time.sleep(1)  # Check every second

if __name__ == "__main__":
    log_application_usage()
