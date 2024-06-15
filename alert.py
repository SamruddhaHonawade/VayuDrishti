import ctypes
import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv()
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

result = supabase.table("Alerts").select("*").execute()

data=pd.DataFrame(result.data)

alter_msg=data['alert'][0]
alert_id=data['id'][0]

# Constants
MB_OKCANCEL = 0x1
MB_ICONQUESTION = 0x20
MB_SYSTEMMODAL = 0x1000

# Function to show message box with two buttons
def show_message():
    # Display the message box
    result = ctypes.windll.user32.MessageBoxW(
        0, f"{alter_msg}", "Alert Message",
        MB_OKCANCEL | MB_ICONQUESTION | MB_SYSTEMMODAL
    )

    # Handle the result
    if result == 1:  # OK button
        print("Action selected")
        
        data=supabase.table("Alert").delete().eq("id",1).execute()
        print(data) 
        
            
            
    elif result == 2:  # Cancel button
        print("Ignore selected")
        # Place your ignore code here

show_message()