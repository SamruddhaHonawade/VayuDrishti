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

# Load environment variables from .env file
load_dotenv()

# Retrieve Supabase URL and Key from environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Create a Supabase client
supabase = create_client(url, key)
role='Developer'

# Define the allowed applications for each role
role_app_access = {
    "Developer": ["pycharm64.exe", "python.exe", "code.exe", "sublime_text.exe", "idea64.exe", "eclipse.exe"],
    "Designer": ["photoshop.exe", "illustrator.exe", "sketch.exe", "figma.exe"],
    "Finance": ["excel.exe", "sheets.exe", "quickbooks.exe"],
    # Add more roles and their allowed applications as needed
}

# Define the maximum allowed access count for each application
app_access_limit = {
    "pycharm64.exe": 20,
    "code.exe": 20,
    "sublime_text.exe": 10,
    "idea64.exe": 10,
    "ApplicationFrameHost.exe":5,
    "eclipse.exe": 10,
    "settings.exe": 5,
    # Add more applications and their access limits as needed
}

# Define a dictionary to keep track of violations
violations = {}
user_name = getpass.getuser()

def capture_photo():
    # Initialize webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True:
            # Read and display frame from webcam
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

# Function to log violations to Supabase
def log_violations(app, duration):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")  # Format timestamp
    count = violations[app]
    supabase.table("violations").insert(
        {"user_name": user_name, "application": app, "violation_count": count, "timestamp": timestamp, "role": role, "duration": duration}
    ).execute()

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

                    # Debug: Print the access count and limit for the current application
                    print(f"Debug: {current_app} - Access Count: {app_access_count[current_app]}, Access Limit: {app_access_limit.get(current_app, 'No limit set')}")

                    # Print an alert if the access count for the current application exceeds its maximum allowed count
                    if current_app in app_access_limit and app_access_count[current_app] > app_access_limit[current_app]:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time
                        # code to Db

                        supabase.table("Alerts").insert(
                            {"alert": f'The application {current_app} has been accessed more than {app_access_limit[current_app]} Times used by {user_name}', "user_name":user_name}
                        ).execute()
                        capture_photo()
                        print(f"Alert: The application {current_app} has been accessed more than {app_access_limit[current_app]} times at {current_time}!")

                    # Check if the current application is allowed for the user's role
                    user_role = supabase.table("user_analysis").select("role").filter("user_name", "eq", user_name).execute().data[0]["role"]
                    if user_role not in role_app_access or current_app not in role_app_access[user_role]:
                        # If the application is not allowed, add it to the violations dictionary
                        if current_app in violations:
                            violations[current_app] += 1
                        else:
                            violations[current_app] = 1
                        print(f"Violation: {user_name} accessed {current_app} which is not allowed for their role {user_role}. Total violations for this app: {violations[current_app]}")
                        log_violations(current_app, duration_minutes)
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
