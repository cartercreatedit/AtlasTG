import datetime
import webbrowser
import pyttsx3
import speech_recognition as sr

engine = pyttsx3.init()
engine.setProperty("rate", 175)  # Adjust speaking speed


def speak(text):
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()


def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"You: {command}")
        return command
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("Speech recognition service is unavailable right now.")
        return ""


def handle_command(command):
    if "hello" in command or "hi jarvis" in command:
        speak("Hello! How can I help you?")
    elif "time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}.")
    elif "date" in command:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {today}.")
    elif "open youtube" in command:
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")
    elif "search for" in command:
        query = command.split("search for", 1)[1].strip()
        if query:
            speak(f"Searching for {query}.")
            webbrowser.open(f"https://google.com{query}")
    elif "stop listening" in command or "goodbye" in command or "exit" in command:
        speak("Shutting down. Talk to you later.")
        return False
    else:
        speak("I heard you, but I don't have a command for that yet.")
    return True


def main():
    speak("Jarvis online. Say 'Hey Jarvis' followed by a command.")
    wake_word = "jarvis"

    while True:
        heard = listen()
        if not heard:
            continue

        if wake_word in heard:
            # If the user said "Jarvis what time is it", handle it right away
            after_wake = heard.split(wake_word, 1)[1].strip()
            if after_wake:
                if not handle_command(after_wake):
                    break
            else:
                speak("Yes?")
                command = listen()
                if command and not handle_command(command):
                    break


if __name__ == "__main__":
    main()
