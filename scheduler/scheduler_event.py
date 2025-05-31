from datetime import datetime
import time
import schedule
from threading import Timer
import threading
import asyncio
import sys
import os
import pickle

data_lock_get_event=threading.Lock()
# Step 1: Add the parent folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calander_api.calander_main import get_data
from telegram_client.main import activate_feature,deactivate_feature,start_telethon,check_users_10_mins,data_lock
# print(events_list)
running_process=False
events_list=None

def cheack_and_run()->None:
    global running_process, events_list

    now= datetime.now().strftime("%H:%M:%S")
    print("Checking calander events")
    events_list=get_data()
    with data_lock:
        with open("data.pkl", "wb") as f:
            pickle.dump(events_list, f)
    print(events_list)
    if events_list != "Error":
        for slots in events_list:
            # print("!")
            # print(slots)
            start_time=datetime.strptime(slots["start"],"%H:%M:%S")
            end_time=datetime.strptime(slots["end"],"%H:%M:%S")
            now_time=datetime.strptime(now,"%H:%M:%S")

            if start_time<=now_time<end_time:
                if not running_process :
                    print("Function handler established")
                    asyncio.run(activate_feature())
                    running_process = True
                    second_left=(end_time-now_time).seconds
                    Timer(second_left,stop_task).start()
                else:
                    print("Process already in action")
                break
        else:
            print("No taks pending")

def stop_task():
    global running_process
    if running_process:
        asyncio.run(deactivate_feature())
        print("Handler stoped")
        running_process=False

def run_scheduler():
    time.sleep(5)
    cheack_and_run()
    print(" check user Function ran first time\n")
    schedule.every(10).minutes.do(cheack_and_run)
    # check user 10 mins , telethon function
    schedule.every(5).minutes.do(check_users_10_mins)
    print("Scheduler started")
    while True:
        schedule.run_pending()
        time.sleep(40)

def run_telethon_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telethon())

def get_user_events_list():
    with data_lock_get_event:
        return events_list

if __name__ == "__main__":
    # Thread for Telethon bot
    telethon_thread = threading.Thread(target=run_telethon_bot, daemon=True)
    telethon_thread.start()

    # Thread for scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Keep main thread alive while both threads run
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Exiting program")
