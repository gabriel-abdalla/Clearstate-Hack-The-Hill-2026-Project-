#installed processes
import win32gui
import win32process
import win32con
import psutil
import socket
import json 
import pygetwindow as gw
import sys
import subprocess
import time
from pathlib import Path

#TO RUN SCRIPT: python.exe "C:\Andrew C\Hackathon\Script Tests\app_monitor.py"

#host data
HOST = "127.0.0.1"
PORT = 5000
PROJECT_DIR = Path(__file__).resolve().parent.parent / "ClearState"
PRESAGE_SCRIPT = PROJECT_DIR / "presage2.py"
LOCKED_APPS_FILE = PROJECT_DIR / "locked_apps.txt"
STATE_FILE = Path(__file__).resolve().parent.parent / "presage_main_run.txt"

@staticmethod
def read_textfile(file_path):
    entries = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # .strip() removes the trailing newline character (\n)
            entry = line.strip()
            if entry:
                entries.append(entry)
    return entries

@staticmethod 
def write_andclear_textfile(file_path, entry):
    with open(file_path, "w", encoding="utf-8") as file:
        pass  # Clear the file by opening it in write mode without writing anything
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(entry) #write the new entry to the file

def minimize_by_keyword(keyword):
    windows = gw.getWindowsWithTitle(keyword)
    for window in windows:
        if window.isMinimized:
            continue  # Skip if the window is already minimized
        window.minimize()
        print(f"Minimized window: {window.title}")
        
def open_presage_process(application):
    # Pause monitoring until the Presage dashboard closes.
    print("Opening Presage authentication...")
    write_andclear_textfile(STATE_FILE, "True")
    minimize_by_keyword(application["window"])
    try:
        presage_process = subprocess.Popen(
            [sys.executable, str(PRESAGE_SCRIPT), "--gui"],
            cwd=PROJECT_DIR,
        )
        while presage_process.poll() is None:
            minimize_by_keyword(application["window"])
            time.sleep(1)
        return presage_process.wait()
    finally:
        write_andclear_textfile(STATE_FILE, "False")

def get_open_applications():
    applications = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return #if window isnt visible skip it (removes background processes)
            
        title = win32gui.GetWindowText(hwnd) #title of window

        if not title:
            return

        try: #try to get the application name and window title, if it fails skip it
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)

            applications.append({
                "name": process.name(), #OPERATION NAME i.e. "chrome.exe"
                "window": title #WINDOW TITLE i.e. "Hackathon - Google Docs"
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    win32gui.EnumWindows(callback, None)

    return applications

def main():
    authorized_window = None

    while True:
        applications = get_open_applications()
        if authorized_window and not any(
            application["window"] == authorized_window for application in applications
        ):
            authorized_window = None
        valid = False
        locked_application = None
        locked_apps = read_textfile(LOCKED_APPS_FILE)  # Read the locked
        for application in applications:
            app_name = application["name"].removesuffix(".exe")
            app_window = application["window"]
           # print(f"Checking application: {app_name}, Window: {app_window}")  # Debugging output
            if app_name in locked_apps:
                valid = True
                locked_application = application
                break  # Exit the loop if a locked application is found
            for locked_app in locked_apps:
                if locked_app.lower() in app_window.lower():
                    valid = True
                    locked_application = application
                    break  # Exit the loop if a locked application is found
        if valid and locked_application["window"] != authorized_window:
            if open_presage_process(locked_application) == 0:
                print(f"Authorized access to {locked_application['window']}.")
                authorized_window = locked_application["window"]
        time.sleep(2)

if __name__ == "__main__":
    main()