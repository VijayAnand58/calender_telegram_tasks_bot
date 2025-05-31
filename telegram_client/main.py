from dotenv import load_dotenv
import os, sys
load_dotenv()

api_id=os.getenv("TELEGRAM_API")
api_hash=os.getenv("TELEGRAM_HASH_ID")

#to Be enved 
# from chatbot.msg_analyzer import Message_analyzer as ma

from telethon import TelegramClient,events

from telethon.tl.types import User

from datetime import datetime

import pickle
client = TelegramClient('anon', api_id, api_hash)

import threading
data_lock=threading.Lock()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot.msg_analyzer import google_task_handler

important_usernames=set()
import os
if os.path.exists("important_users.pkl"):
    with open("important_users.pkl", "rb") as f:
        important_usernames_set= pickle.load(f)
        important_usernames.update(important_usernames_set)

visited_id={}
@client.on(events.NewMessage(outgoing=True))
async def admin_handler(event):
    me= await client.get_me()
    if event.chat_id != me.id:
        return 400  
    msg = event.raw_text.strip()
    parts = msg.split(maxsplit=1)
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else None

    if command == "/add_important":
        if argument:
            important_usernames.add(argument.lstrip('@').lower())
            with open("important_users.pkl","+bw") as f:
                pickle.dump(important_usernames,f)
            await event.respond(f"Added @{argument} to important users.")
        else:
            await event.respond("Please specify a username.")

    elif command == "/remove_important":
        if argument:
            important_usernames.discard(argument.lstrip('@').lower())
            with open("important_users.pkl","+bw") as f:
                pickle.dump(important_usernames,f)
            await event.respond(f"Removed @{argument} from important users.")
        else:
            await event.respond("Please specify a username.")

    elif command == "/list_important":
        if important_usernames:
            await event.respond("Important Users:\n" + "\n".join(f"@{u}" for u in important_usernames))
        else:
            await event.respond("No important users added yet.")

    else:
        await event.respond("Unknown admin command.")

# from scheduler.scheduler_event import get_user_events_list 
async def handle_message(event)->None:
    # print(important_usernames)
    sender=await event.get_sender()
    sender_id=sender.id
    # print(sender)
    if sender.username:
        sender_username:str=(sender.username.lower())
    else:
        sender_username:str="no username"

    print(f"sender id is {sender_id}, username is {sender_username}")

    if isinstance(sender,User) and not sender.bot and event.is_private:
        # check whether the user is important or not
        is_important:bool= (sender_username in important_usernames)

        already_visited=visited_id.get(sender_id,None)
        if not already_visited:
            visited_id[sender_id]=datetime.now()

        if is_important:
            msg:str=event.raw_text.strip()
            parts=msg.split(maxsplit=1)

            #parse message parts
            command:str=parts[0].lower()
            content:str=parts[1] if len(parts)>1 else None

            if command == "/bot":
                if content is not None:
                    temp_resut=google_task_handler(content)
                    if temp_resut == 300:
                        await event.respond(f"Task Not Added or internal server error")
                    else:
                        await event.respond(f"Task added")
                else:
                    await event.respond("No content given")
            else:
                if not already_visited:
                    with data_lock:
                        with open("data.pkl", "rb") as f:
                            temp_list_events= pickle.load(f)
                            print(temp_list_events)
                            if temp_list_events != "Error":
                                for temps in temp_list_events:
                                    temp_start_time=datetime.strptime(temps["start"],"%H:%M:%S")
                                    temp_end_time=datetime.strptime(temps["end"],"%H:%M:%S")
                                    temp_now=datetime.strptime(datetime.now().strftime("%H:%M:%S"),"%H:%M:%S")

                                    if temp_start_time<=temp_now<temp_end_time:
                                        temps_string=""
                                        for words in temps["events"]:
                                            temps_string=temps_string+","+ words
                                        s=f"""Bot: This is an automated message. The user is busy from {temps['start']} to {temps['end']} on works like {temps_string}\n
To send any tasks to the user, please use /bot.\n Please try to mention the task like 'Your Task is ...' """
                                        await event.respond(s)
                                        break
                            else:
                                await event.respond("Bot: This is automated message, user is in work, please wait")
        else:
            if not already_visited:
                await event.respond("Bot: This is an automated message.\n User is busy, please contact later")
        

FEATURE_ACTIVE:bool=False
async def activate_feature():
    global FEATURE_ACTIVE
    print("activate Feature")
    if not FEATURE_ACTIVE:
        client.add_event_handler(handle_message,events.NewMessage(incoming=True))
    FEATURE_ACTIVE= True
    print("Global Tele bot handler Active")

async def deactivate_feature():
    global FEATURE_ACTIVE
    if FEATURE_ACTIVE:
        client.remove_event_handler(handle_message,events.NewMessage(incoming=True))
    FEATURE_ACTIVE=False
    print("Gloabal Telebot disconnected")
 
async def start_telethon():
    await client.start()
    print(f"Bot started at {datetime.time}")
    # # client.loop.run_until_complete(get_id())
    await client.run_until_disconnected()

def check_users_10_mins():
    if len(visited_id)<=0: return

    time_now_check=datetime.now()
    for visitor_id_instance, time_int in visited_id.items():
        if ((time_now_check-time_int).total_seconds() / 60) >= 10:
            del visited_id[visitor_id_instance] 