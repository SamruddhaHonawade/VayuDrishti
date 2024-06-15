from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"Alert: File created: {event.src_path}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        print(f"Alert: File deleted: {event.src_path}")

    def on_moved(self, event):
        print(f"Alert: File moved from {event.src_path} to {event.dest_path}")

def monitor_directory(path):
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)  # Set recursive=True to monitor subdirectories as well
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:  
        observer.stop()
    observer.join()

if __name__ == "__main__":
    directory_to_watch = "C:/Users/aswin/Desktop"
    print(f"Monitoring directory: {directory_to_watch}")
    monitor_directory(directory_to_watch)