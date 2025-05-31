
#  credits : google example for the usage of calander

from datetime import datetime,time,timedelta,timezone
from zoneinfo import ZoneInfo
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

india=ZoneInfo("Asia/Kolkata")
today = datetime.now(india).date()
start_of_day = datetime.combine(today, time.min, tzinfo=india)
end_of_day = datetime.combine(today, time.max, tzinfo=india)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly",'https://www.googleapis.com/auth/tasks']

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.now(tz=india).isoformat()
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return 400
    
    def timeparser(s:str)->str:
      if "T" in s:
        timepart=s.split("T")[1]
        timeonly=timepart.split("+")[0]
        return timeonly
      else:
        return None
      
    list_of_events=list()

    for event in events:
      start = timeparser(event["start"].get("dateTime", event["start"].get("date")))
      end = timeparser(event["end"].get("dateTime",event["start"].get("date")))
      summary=event["summary"]
      list_of_events.append([summary ,start, end])
    # print(event)
    print(list_of_events)
    return list_of_events

  except HttpError as error:
    print(f"An error occurred: {error}")
    return 400
  

def merge_busy_periods_with_events(event_list):
    # Convert to datetime and keep track of original names
    if event_list != 400:
      time_ranges = []
      for name, start, end in event_list:
          start_dt = datetime.strptime(start, "%H:%M:%S")
          end_dt = datetime.strptime(end, "%H:%M:%S")
          time_ranges.append((start_dt, end_dt, name))

      # Sort by start time
      time_ranges.sort()

      merged = []
      for start, end, name in time_ranges:
          if not merged:
              merged.append({
                  "start": start,
                  "end": end,
                  "events": [name]
              })
          else:
              last = merged[-1]
              if start <= last["end"]:  # Overlapping
                  last["end"] = max(last["end"], end)
                  last["events"].append(name)
              else:
                  merged.append({
                      "start": start,
                      "end": end,
                      "events": [name]
                  })

      # Convert times back to strings
      for slot in merged:
          slot["start"] = slot["start"].strftime("%H:%M:%S")
          slot["end"] = slot["end"].strftime("%H:%M:%S")
      return merged
    else:
       return "Error"

def add_tasks(data_dict:dict):
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  try:
    service=build('tasks','v1',credentials=creds)
    if data_dict['is_task']:
      data_title=data_dict['title']
      data_date_time=isotime_coverter(date_val=data_dict['date'],time_val=data_dict['time'])
      task={
           'title':data_title,
           'due':data_date_time,
           'notes':"Added by Telebot"
        }
      service.tasks().insert(tasklist='@default',body=task).execute()
    else:
       return 300
  except HttpError as error:
     print(f"Error has occured and it is {error}")
     return 400

import pytz  
def isotime_coverter(date_val,time_val):
  time_zone="Asia/Kolkata"
  datetime_str=f"{date_val} {time_val}"
  dt_initial=datetime.strptime(datetime_str,"%d-%m-%Y %H:%M")

  local_tz=pytz.timezone(time_zone)
  dt_local=local_tz.localize(dt_initial)
  dt_utc= dt_local.astimezone(pytz.utc)

  g_task_format= dt_utc.isoformat()
  return g_task_format

# print(isotime_coverter("31-05-2025","12:39:00")) testing

def get_data()->list:
  return merge_busy_periods_with_events(main()) 

  