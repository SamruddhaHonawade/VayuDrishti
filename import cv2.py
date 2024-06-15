import cv2
import time
from dotenv import load_dotenv
import os
import random
from supabase import create_client, Client
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

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
        r_num = random.randint(1,10)
        fileimg_name="user1"+str(r_num)+".png"
        data = supabase.storage.from_(bucket_name).upload(fileimg_name, new_file)
        print(data)

if __name__ == "__main__":
    capture_photo()
