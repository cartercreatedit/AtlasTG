import streamlit as st
from groq import Groq
import datetime
import base64
import requests
import re

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================
# GROQ
# =========================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = ""

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "speech_to_play" not in st.session_state:
    st.session_state.speech_to_play = ""

# =========================
# CURRENT TIME
# =========================
now = datetime.datetime.now()
current_time = now.strftime("%I:%M %p")
current_date = now.strftime("%A, %B %d, %Y")

# =========================
# WEATHER
# =========================
def get_weather(location: str = "") -> str:
    try:
        if not location or location.lower() in ["here", "my location", "current", ""]:
            url = "https://wttr.in/?format=3"
        else:
            loc = location.strip().replace(" ", "+")
            url = f"https://wttr.in/{loc}?format=3"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.text.strip()
        return "I'm afraid I couldn't retrieve the weather data at the moment, sir."
    except Exception:
        return "I'm afraid I couldn't retrieve the weather data at the moment, sir."

# =========================
# AI
# =========================
def ask_jarvis(user_text: str) -> str:
    if not client:
        return "I'm afraid my connection is currently offline, sir."

    weather_match = re.search(
        r"(?:weather|temperature|forecast|how's the weather|how is the weather|is it (?:raining|sunny|cold|hot|warm)).*?(?:in|at|for)?\s*([A-Za-z\s]+)?",
        user_text,
        re.IGNORECASE
    )

    extra_context = ""
    if weather_match:
        location = weather_match.group(1).strip() if weather_match.group(1) else ""
        weather_info = get_weather(location)
        extra_context = f"\n\nReal-time weather information: {weather_info}\nUse this data accurately."

    system_prompt = f"""
You are J.A.R.V.I.S., Tony Stark's personal AI assistant.

Rules:
- Always address the user as "sir".
- Speak calmly, formally and with a British tone.
- Keep responses short and natural for speech (1–3 sentences).
- Do not say "You're most welcome", "Is there anything else?", or similar filler.
- Sound like the Jarvis from the Iron Man films.

Current date: {current_date}
Current time: {current_time}
{extra_context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-8:])
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.55,
            max_tokens=220
        )
        answer = response.choices[0].message.content.strip()

        for phrase in ["You're most welcome.", "You're welcome.", "Is there anything else I can help you with?", "Is there anything else?"]:
            if answer.endswith(phrase):
                answer = answer[:-len(phrase)].strip()

        return answer
    except Exception as e:
        return f"I encountered a technical issue, sir. {str(e)}"

# =========================
# TRANSCRIBE
# =========================
def transcribe_audio(audio_bytes):
    if not client:
        return None
    try:
        result = client.audio.transcriptions.create(
            file=("voice.webm", audio_bytes),
            model="whisper-large-v3-turbo",
            response_format="json"
        )
        return result.text.strip()
    except Exception:
        try:
            result = client.audio.transcriptions.create(
                file=("voice.mp4", audio_bytes),
                model="whisper-large-v3-turbo",
                response_format="json"
            )
            return result.text.strip()
        except Exception as e:
            st.error(f"Voice recognition error: {e}")
            return None

# =========================
# STYLING
# =========================
st.markdown("""
<style>
    .stApp { background: #050505; }
    .title {
        text-align: center;
        color: #00d4ff;
        font-size: 32px;
        letter-spacing: 10px;
        margin: 50px 0 10px 0;
        font-weight: 200;
    }
    .status {
        text-align: center;
        color: #888;
        font-size: 14px;
        letter-spacing: 1.5px;
        margin: 15px 0 30px 0;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# UI
# =========================
st.markdown('<div class="title">J.A.R.V.I.S.</div>', unsafe_allow_html=True)

if st.session_state.is_recording:
    st.markdown('<div class="status">RECORDING... TAP AGAIN TO STOP</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status">TAP TO SPEAK</div>', unsafe_allow_html=True)

# =========================
# RECORDING BUTTON
# =========================
audio_data = st.audio_input(
    "Tap to speak",
    key="jarvis_mic",
    label_visibility="collapsed"
)

# =========================
# PROCESS AUDIO
# =========================
if audio_data is not None:
    audio_bytes = audio_data.read()

    with st.spinner("Processing..."):
        spoken_text = transcribe_audio(audio_bytes)

        if spoken_text:
            st.session_state.messages.append({"role": "user", "content": spoken_text})
            answer = ask_jarvis(spoken_text)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.speech_to_play = answer

            # Show what was said + reply
            st.markdown(f"**You:** {spoken_text}")
            st.markdown(f"**J.A.R.V.I.S.:** {answer}")

            # Speak the reply using browser TTS
            st.components.v1.html(f"""
            <script>
                const text = {repr(answer)};
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.88;
                utterance.pitch = 0.80;
                window.speechSynthesis.speak(utterance);
            </script>
            """, height=0)

# =========================
# CLEAR old speech
# =========================
if st.session_state.speech_to_play:
    st.session_state.speech_to_play = ""
