from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re
load_dotenv()
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calander_api.calander_main import add_tasks

def extract_json_from_text(text):
    # Remove triple backticks and any language hints (e.g., ```json)
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"```", "", cleaned)

    # Sometimes JSON is enclosed in single or double quotes by mistake, remove those
    cleaned = cleaned.strip().strip('\'"')

    # Try to parse JSON
    return json.loads(cleaned)

def analyze_msg(chat_text)->dict:
    
    genai.configure(api_key=os.getenv("GOOGLE_API"))
    model=genai.GenerativeModel('gemini-2.0-flash')

    today_date=datetime.today().strftime("%d-%m-%y")
    time_now=datetime.now().strftime("%H:%M:%S")

    prompt = f"""
Today's date is {today_date}.
Time Now is {time_now}.

You are an assistant that extracts task-related data from chat messages.
Even if the message is informal or conversational (e.g., includes words like "bro", "hey", or lacks punctuation), 
still treat it as a task if it contains a clear action and a time or deadline.
Given a message, determine if it's assigning a task. If so, return a JSON object with:

- is_task: true/false
- title: a short paraphrased task description
- date: extracted or inferred date (in DD-MM-YYYY format)
- time: extracted or inferred time (in HH:MM 24-hour format)
- original_text: the full original chat message

Examples of tasks:
- "Can you please send the report?"
- "Please visit the doctor this afternoon"
- "Could you check the mail tomorrow?"

Examples of non-tasks:
- "What are you doing?"
- "Let’s talk later"

Note: Messages like "Can you please visit the doctor afternoon" should be treated as tasks even if informal or slightly vague.

Important:
- Even if the message does not use verbs like "please" or "can you", treat it as a task if it says things like:
  - "your task is..."
  - "you need to..."
  - "you have to..."
- These should always be interpreted as task assignments.

Rules:
1. If the message **does not mention a date**, assume it is for **today**.
2. If the message **does not mention a time**, assume the task should be done **two hours from now** based on current time.
3. Accept vague or informal phrasing such as "bro", "hey", "plz", etc., as valid if there's a clear action.

If it's not a task, return:
{{ "is_task": false, "original_text": "{chat_text}" }}

Message: "{chat_text}"
Respond ONLY with a raw JSON object. Do not wrap it in code blocks or add explanations.
"""
    response = model.generate_content(prompt)
    try:
        return extract_json_from_text(response.text)  
    except Exception as e:
        return {"error": "Invalid response", "raw_output": response.text, "exception": str(e)}

# print(analyze_msg("Hey , vijay, your task is to go to the covention centerr and deliver goods after 2 pm today"))
# Test succesful
def google_task_handler(msg:str):
    try:
        result_llm=analyze_msg(msg)
        result_add=add_tasks(result_llm)
        if result_add==300:
            return 300
    except Exception as e:
        print("Error in google tasks handler")
        return 400

