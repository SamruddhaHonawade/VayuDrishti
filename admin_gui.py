import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
import os
from dotenv import load_dotenv
from matplotlib.figure import Figure
from supabase import create_client
import schedule
import threading
import ctypes
import time
import os
import matplotlib.dates as mdates


load_dotenv()

MB_OKCANCEL = 0x1
MB_ICONQUESTION = 0x20
MB_SYSTEMMODAL = 0x1000


url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")


supabase = create_client(url, key)
data = supabase.table("violations").select("*").execute().data


df = pd.DataFrame(data)
data2 = supabase.table("user_analysis").select("*").execute().data
df2 = pd.DataFrame(data2)
data3 = supabase.table("code_vulnerabilities").select("*").execute().data
df3 = pd.DataFrame(data3)


df['timestamp'] = pd.to_datetime(df['timestamp'])


max_violation_indices = df.groupby(['user_name', 'application'])['violation_count'].idxmax()


df_max_violations = df.loc[max_violation_indices]

def create_vulnerabilities_table(user):
    user_data = df3[df3['user_name'] == user]
    return user_data

def display_vulnerabilities_table(frame, user):
    for widget in frame.winfo_children():
        widget.destroy()

    user_data = create_vulnerabilities_table(user)

    style = ttk.Style()
    style.configure("Treeview",
                    background="lightgray",
                    foreground="black",
                    rowheight=25,
                    fieldbackground="lightgray")
    style.map('Treeview', background=[('selected', 'darkgray')])
    style.configure("Treeview.Heading",
                    background="gray",
                    foreground="black",
                    padding=10)

    tree = ttk.Treeview(frame, style="Treeview")
    tree["columns"] = list(user_data.columns)
    tree["show"] = "headings"

    for column in user_data.columns:
        tree.heading(column, text=column)
        
        if column == user_data.columns[0] or column == user_data.columns[1] or column == user_data.columns[3] or column == user_data.columns[4]:
            tree.column(column, width=70, anchor='center')
        
        elif column == user_data.columns[5]:
            tree.column(column, width=350)
        else:
            tree.column(column, width=100, anchor='center')

    for index, row in user_data.iterrows():
        tree.insert("", "end", values=list(row))

    tree.pack(fill='both', expand=True)


def plot_violated_applications_time(user):
    user_df = df_max_violations[df_max_violations['user_name'] == user]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(user_df['application'], user_df['duration'])  # Change to horizontal bar chart
    ax.set_ylabel('Application')  # Swap x and y labels
    ax.set_xlabel('Duration (minutes)')
    ax.set_title(f'Violated Applications Opened and Time Used by {user}')
    return fig

def plot_violation_application_opened(user):
    user_df = df_max_violations[df_max_violations['user_name'] == user]
    app_counts = user_df.groupby('application')['violation_count'].sum()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(app_counts, labels=app_counts.index, autopct=lambda p: '{:,.0f}'.format(p * sum(app_counts) / 100), textprops={'fontsize': 'x-small'})
    ax.set_title(f'Number of Times Each Violation Application is Opened by {user}')
    return fig

def plot_activity_time_over_range(user):
    user_data = df2[df2['user_name'] == user]
    user_activity_time = user_data.groupby('log_time')['duration'].sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    user_activity_time.plot(kind='line', ax=ax)
    ax.set_xlabel('Time')
    ax.set_ylabel('Duration (Minutes)')
    ax.set_title(f'Activity Over Time for {user}')

    plt.setp(ax.get_xticklabels(), fontsize='x-small')

    return fig

def plot_application_usage_duration(user):
    user_data = df2[df2['user_name'] == user]
    applications = user_data['application'].unique()
    durations = [user_data[user_data['application'] == app]['duration'].sum() for app in applications]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(applications, durations, label='Duration', color=np.random.rand(len(applications), 3))
    ax.set_xlabel('Applications')
    ax.set_ylabel('Duration (Minutes)')
    ax.set_title(f'Application Usage Duration for {user}')
    ax.set_xticks(applications)
    ax.set_xticklabels(applications, rotation=45, fontsize='x-small')
    ax.legend()

    return fig

def plot_application_user_counts():
    fig, ax = plt.subplots(figsize=(10, 6))
    app_counts = df_max_violations['application'].value_counts()

    ax.bar(app_counts.index, app_counts.values, label='Users', color=np.random.rand(len(app_counts.index), 3))
    ax.set_xlabel('Applications')
    ax.set_ylabel('Number of Users')
    ax.set_title('Number of Users Using Each Application')
    ax.set_xticks(app_counts.index)
    ax.set_xticklabels(app_counts.index, rotation=45, fontsize='x-small')
    ax.legend()

    return fig

# Function to display the plot in a given frame
def display_plot(frame, plot_func, user=None):
    for widget in frame.winfo_children():
        widget.destroy()
    if user:
        fig = plot_func(user)
    else:
        fig = plot_func()
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


def show_main_app():
    global root
    root = tk.Tk()
    root.title("User Violation Analysis")

    # Create a frame for the buttons
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

   
    display_frame = tk.Frame(root)
    display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    users = df_max_violations['user_name'].unique()

    
    for user in users:
        button = tk.Button(button_frame, text=user, command=lambda u=user: create_user_interface(u, display_frame), width=20, height=2)
        button.pack(pady=5)

   
    root.mainloop()


def create_user_interface(user, display_frame):
    # Clear the display frame
    for widget in display_frame.winfo_children():
        widget.destroy()

  
    tab_control = ttk.Notebook(display_frame)
    tab_control.pack(expand=1, fill="both")

    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    tab3 = ttk.Frame(tab_control)
    tab4 = ttk.Frame(tab_control)
    tab5 = ttk.Frame(tab_control)
    tab6 = ttk.Frame(tab_control)

    tab_control.add(tab1, text="Violated Applications Time")
    tab_control.add(tab2, text="Violation Application Opened")
    tab_control.add(tab3, text="Activity Time Over Range")
    tab_control.add(tab4, text="Application Usage Duration")
    tab_control.add(tab5, text="Application User Counts")
    tab_control.add(tab6, text="Code Vulnerabilities")

    # Display plots in each tab
    display_plot(tab1, plot_violated_applications_time, user)
    display_plot(tab2, plot_violation_application_opened, user)
    display_plot(tab3, plot_activity_time_over_range, user)
    display_plot(tab4, plot_application_usage_duration, user)
    display_plot(tab5, plot_application_user_counts)
    display_vulnerabilities_table(tab6, user)

def login():
    username = username_entry.get()
    password = password_entry.get()
    if username == "admin" and password == "adminfriend":
        login_window.destroy()
        show_main_app()
    else:
        messagebox.showerror("Error", "Not an admin")

# Create the login window
login_window = tk.Tk()
login_window.title("Login")

tk.Label(login_window, text="Username:").pack(pady=5)
username_entry = tk.Entry(login_window)
username_entry.pack(pady=5)

tk.Label(login_window, text="Password:").pack(pady=5)
password_entry = tk.Entry(login_window, show="*")
password_entry.pack(pady=5)

login_button = tk.Button(login_window, text="Login", command=login)
login_button.pack(pady=20)

def show_message():
    try:
        result = supabase.table("Alerts").select("*").execute()
        data = pd.DataFrame(result.data)
        alert_msg = data['alert'][0]
        alert_id = data['id'][0]

        # Display the message box
        result = ctypes.windll.user32.MessageBoxW(
            0, f"{alert_msg}", "Alert Message",
            MB_OKCANCEL | MB_ICONQUESTION | MB_SYSTEMMODAL
        )

       
        if result == 1:  # OK button
            print("Action selected")
            data = supabase.table("Alerts").delete().eq("id", alert_id).execute()
        elif result == 2:  # Cancel button
            print("Ignore selected")
    except Exception as e:
        print(e)

#  every 5 sec
schedule.every(5).seconds.do(show_message)

#  separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# Start the GUI event loop for the login window
login_window.mainloop()
