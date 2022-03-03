from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import time
import pyttsx3
import speech_recognition as sr 
import pytz
import subprocess
import requests
from bs4 import BeautifulSoup



SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september","october", "november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_EXTENTIONS = ["rd", "th", "st", "nd"]


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception: " + str(e))

    return said.lower()



def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    return service


def get_events(day, service):
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())     # minimum time (start time-12am)
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())     # maximum time(end time-11:59pm)
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)     # utc formatted date string

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(), singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    

    if not events:
        speak('No upcoming events found.')
        print("No upcoming events found.")
    else:
        speak(f"You have {len(events)} events on this day.")
        print(f"You have {len(events)} events on this day.")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("-")[0])     # get the hour the event starts
            if int(start_time.split(":")[0]) < 12:      # if the event is in the morning
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12) +  start_time.split(":")[1] # convert 24 hour time to regular (7pm instead of 19pm) + minutes
                start_time = start_time + "pm"  

            speak(event["summary"] + " at " + start_time)


def get_date(text):
    today = datetime.date.today()   #Date object
    if text.count("today") > 0:
        return today                #Returning today's date

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1      #finiding month/day number
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENTIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])     #slice extention out of date (store only 5 from 5th)
                    except:
                        pass

    if month < today.month and month != -1:  # if the month mentioned is before the current month set the year to the next
        year = year+1

    if month == -1 and day != -1:  # if we didn't find a month, but we have a day
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    if month == -1 and day == -1 and day_of_week != -1:     # if there is only a day in the input ("Tuesday")
        current_day_of_week = today.weekday()       # Which day of the week it is today (in index 0-6)
        dif = day_of_week - current_day_of_week

        if dif < 0:
            dif += 7
            if text.count("next") >= 1:     # skipping one week (not this saturday, next)
                dif += 7

        return today + datetime.timedelta(dif)      # return date object after adding

    if day != -1: 
        return datetime.date(month=month, day=day, year=year)       # return finall full date

def note(text):
    date = datetime.datetime.now()      # current date and time
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name, "w") as f:
        f.write(text)
    sublime = "/Users/reembadami/Desktop/PythonProject/"+file_name
    subprocess.call(['open', sublime])

WAKE = "nacho"
SERVICE = authenticate_google()
print("Power on")

while True:
    print("Listening")
    text = get_audio()

    if text.count(WAKE) > 0:
        speak("Hi Reem")
        print("Hi Reem")
        text = get_audio()

        CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy", "whats my day like", "whats the schedule"]
        for phrase in CALENDAR_STRS:
            if phrase in text:
                date = get_date(text)
                if date:
                    get_events(date, SERVICE)
                else:
                    speak("I don't understand")

        NOTE_STRS = ["make a note", "write this down", "remember this", "type this", "save this", "new note", "add note", "note this down"]
        for phrase in NOTE_STRS:
            if phrase in text:
                speak("What would you like me to write down?")
                print("What would you like me to write down?")
                note_text = get_audio()
                note(note_text)
                speak("I've made a note of that.")
                print("I've made a note of that.")

        APP_STRS = ["safari", "spotify", "app store", "zoom"]
        for phrase in APP_STRS:
            if phrase in text:
                if phrase == APP_STRS[0]:
                    os.system("open /Applications/Safari.app")
                elif phrase == APP_STRS[1]:
                    os.system("open /Applications/Spotify.app")
                elif phrase == APP_STRS[2]:
                    os.system("open /System/Applications/App Store.app")
                elif phrase == APP_STRS[3]:
                    os.system("open /Applications/zoom.us.app")

        if text == "goodbye":
            quit()

        words = text.split()
        if words[0] == 'google':
            command = 'https://www.google.com/search?q='+'+'.join(words[1:])
            source =  requests.get(command).text
            soup= BeautifulSoup(source,'lxml')
            speak(soup.find_all('div', {'class': 'BNeawe'})[0].text)
            print(soup.find_all('div', {'class': 'BNeawe'})[0].text)