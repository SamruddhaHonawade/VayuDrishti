from dotenv import load_dotenv
import os
from supabase import create_client, Client
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

data = supabase.table("user_analysis").select("*").execute()
df = pd.DataFrame(data.data)
users = df['user_name'].unique()

for user in users:
    user_data = df[df['user_name'] == user]
    applications = user_data['application'].unique()
    durations = [user_data[user_data['application'] == app]['duration'].sum() for app in applications]
    
    # Setting position and width for the bars
    positions = np.arange(len(applications))
    width = 0.35
    
    plt.figure(figsize=(10, 6))
    plt.bar(positions, durations, width, label='Duration', color=np.random.rand(len(applications),3))
    
    plt.xlabel('Applications')
    plt.ylabel('Duration (Minutes)')
    plt.title(f'Application Usage Duration for {user}')
    plt.xticks(positions, applications, rotation=45)
    plt.legend()
    
    plt.tight_layout()
    plt.show()


for user in df['user_name'].unique():
    user_data = df[df['user_name'] == user]
    user_activity_time = user_data.groupby('log_time')['duration'].sum()
    user_activity_time.plot(kind='line', title=f'Activity Over Time for {user}')
    plt.xlabel('Time')
    plt.ylabel('Duration (Minutes)')
    plt.show()
    

app_access_counts = df.groupby('application')['access_count'].sum()
app_access_counts.plot(kind='pie', autopct=lambda p: '{:,.0f}'.format(p * sum(app_access_counts) / 100))
plt.title('Application Access Counts')
plt.ylabel('')
plt.show()