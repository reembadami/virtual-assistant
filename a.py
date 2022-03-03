import speech_recognition as sr
import requests
from bs4 import BeautifulSoup
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Speak: ")
    audio_data = r.listen(source)
    try:
        text = r.recognize_google(audio_data).lower()
        print(text)
    except:
        print("Couldn't recognize")
words = text.split()
if words[0] == 'google':
    command = 'https://www.google.com/search?q='+'+'.join(words[1:])
    source =  requests.get(command).text
    soup= BeautifulSoup(source,'lxml')
    print(soup.find_all('div', {'class': 'BNeawe'})[0].text)