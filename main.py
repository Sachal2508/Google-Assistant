"""
================================================================
 A replica version of Google's voice assistant
================================================================

================================================================
 REQUIRED MODULES – Install before running (using pip):
================================================================
Create an env file before installing all these modules

pip install speechrecognition pocketsphinx gTTS pygame pyttsx3 requests
pip install openai==1.*          # Official OpenAI SDK v1
pip install pyjokes              # For jokes
pip install wikipedia
Optional:
- Ensure you have a `musicLibrary.py` file with a dictionary:
  music = {"song name": "YouTube URL"}
Notes:
- You need a microphone to give voice commands.
- Replace placeholder API keys (OpenAI, News API, Weather API) with real ones.
================================================================

"""
import os
import time
import datetime
import webbrowser
import requests
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import pygame
import pyjokes
import wikipedia
from openai import OpenAI
import musicLibrary
import openai as _openai

OPENAI_API_KEY = "Enter your openai api"
NEWS_API_KEY = "Enter your news api"
WEATHER_API_KEY = "Enter your weather api"
WAKE_WORDS = {"google", "hi", "hey google"}

_tts_engine = pyttsx3.init()

def speak(text: str, slow: bool = False) -> None:
    try:
        tts = gTTS(text=text, lang="en", slow=slow)
        tmp = "tmp_tts.mp3"
        tts.save(tmp)
        pygame.mixer.init()
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        os.remove(tmp)
    except Exception:
        _tts_engine.say(text)
        _tts_engine.runAndWait()

_ai_client = OpenAI(api_key=OPENAI_API_KEY)

def chat_with_openai(prompt: str) -> str:
    try:
        resp = _ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Google assistant, a friendly virtual assistant. Give concise answers."},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content.strip()
    except _openai.AuthenticationError:
        return "The language service credentials are invalid."
    except Exception:
        return "I couldn't reach the language service."

def run_command(cmd: str) -> None:
    cmd_low = cmd.lower()

    shortcuts = {
        "open google": "https://google.com",
        "open facebook": "https://facebook.com",
        "open youtube": "https://youtube.com",
        "open linkedin": "https://linkedin.com",
    }
    for key, url in shortcuts.items():
        if key in cmd_low:
            webbrowser.open(url)
            speak(f"Opening {key.split()[1]}")
            return

    if cmd_low.startswith("play "):
        song_name = cmd_low[5:].strip()
        url = musicLibrary.music.get(song_name)
        if url:
            speak(f"Playing {song_name}")
            webbrowser.open(url)
        else:
            speak(f"Sorry, I can’t find {song_name} in your library.")
        return

    if "joke" in cmd_low:
        speak(pyjokes.get_joke())
        return

    if "news" in cmd_low:
        try:
            r = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "in", "apiKey": NEWS_API_KEY},
                timeout=6
            )
            r.raise_for_status()
            articles = r.json().get("articles", [])[:5]
            if not articles:
                speak("No headlines at the moment.")
            for art in articles:
                speak(art["title"])
        except requests.RequestException:
            speak("I couldn’t reach the news service right now.")
        return

    if "time" in cmd_low:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")
        return

    if "weather" in cmd_low:
        api_key = WEATHER_API_KEY
        city = "Lahore"       # Enter your city for which you want updates about
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            res = requests.get(url, timeout=6).json()
            temp = res["main"]["temp"]
            desc = res["weather"][0]["description"]
            speak(f"The temperature in {city} is {temp}°C with {desc}")
        except Exception:
            speak("Weather information is unavailable right now.")
        return

    if "who is" in cmd_low or "what is" in cmd_low:
        topic = cmd_low.replace("who is", "").replace("what is", "").strip()
        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except Exception:
            speak("Sorry, I couldn't find that.")
        return

    if "remind me in" in cmd_low:
        try:
            mins = int(cmd_low.split("remind me in")[-1].strip().split()[0])
            speak(f"Okay, I’ll remind you in {mins} minutes.")
            time.sleep(mins * 60)
            speak("Time’s up!")
        except ValueError:
            speak("I didn't understand the time for the reminder.")
        return

    if "remember" in cmd_low and "what did you remember" not in cmd_low:
        note = cmd_low.split("remember")[-1].strip()
        try:
            with open("assistant_memory.txt", "a") as f:
                f.write(note + "\n")
            speak("Noted.")
        except Exception:
            speak("I couldn't save that.")
        return

    if "what did you remember" in cmd_low:
        try:
            with open("assistant_memory.txt", "r") as f:
                memories = f.readlines()
            if memories:
                speak("Here's what I remember:")
                for mem in memories:
                    speak(mem.strip())
            else:
                speak("I don't remember anything yet.")
        except FileNotFoundError:
            speak("I don't have any memories yet.")
        return

    if "shutdown" in cmd_low:
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
        return

    if "restart" in cmd_low:
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")
        return

    if "log out" in cmd_low:
        speak("Logging out.")
        os.system("shutdown /l")
        return

    reply = chat_with_openai(cmd)
    speak(reply)

def listen_for_speech(timeout: int = 3, phrase_limit: int = 5) -> str | None:
    recog = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            audio = recog.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
        return recog.recognize_google(audio)
    except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError, KeyboardInterrupt):
        return None
    except Exception:
        return None

def main():
    speak("Google assistant online.")
    while True:
        try:
            heard = listen_for_speech(timeout=5, phrase_limit=3)
            if not heard:
                continue
            print("Heard:", heard)
            if heard.lower() in WAKE_WORDS:
                speak("Yes sir?")
                cmd = listen_for_speech(timeout=6, phrase_limit=8)
                if cmd:
                    print("Command:", cmd)
                    run_command(cmd)
                else:
                    speak("I did not catch that.")
            time.sleep(0.3)
        except KeyboardInterrupt:
            speak("Goodbye.")
            break
        except Exception as e:
            print("Error:", e)
            speak("Something went wrong, but I’m still running.")

if __name__ == "__main__":
    main()

