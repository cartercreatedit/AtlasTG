import streamlit as st
from groq import Groq
import datetime
import base64
import requests
import re
import os
import streamlit.components.v1 as components
from duckduckgo_search import DDGS

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================
# GROQ & ELEVENLABS CREDENTIALS
# =========================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = ""

eleven_key = st.secrets.get("ELEVEN_API_KEY") or os.getenv("ELEVEN_API_KEY") or ""
voice_id = st.secrets.get("ELEVEN_VOICE_ID") or "bfGb7JTLUnZebZRiFYyq"

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False
if "speech_to_play" not in st.session_state:
    st.session_state.speech_to_play = ""
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""
if "audio_out" not in st.session_state:
    st.session_state.audio_out = None

# Automatically trigger audio streaming if bytes are ready
if st.session_state.audio_out:
    st.markdown(st.session_state.audio_out, unsafe_allow_html=True)
    st.session_state.audio_out = None

# =========================
# CURRENT TIME
# =========================
now = datetime.datetime.now()
current_time = now.strftime("%I:%M %p")
current_date = now.strftime("%A, %B %d, %Y")

# =========================
# HELPERS
# =========================
def get_weather(location: str = "") -> str:
    try:
        location = (location or "").strip()
        for word in ["the", "city", "of", "weather", "in", "at", "for", "please", "current"]:
            location = re.sub(rf"\b{word}\b", "", location, flags=re.IGNORECASE).strip()
        location = re.sub(r"\s+", " ", location).strip()

        if not location or location.lower() in ["here", "my location", "nearby", "outside"]:
            urls = ["https://wttr.in"]
        else:
            clean = location.replace(" ", "+")
            urls = [f"https://wttr.in{clean}?format=3", f"https://wttr.in~{clean}?format=3"]

        for url in urls:
            try:
                r = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and "Unknown location" not in r.text:
                    return r.text.strip().replace("+", " ")
            except:
                continue
        return "I currently don't have reliable weather data for that location, sir."
    except:
        return "I currently don't have reliable weather data, sir."

def web_search(query: str, max_results: int = 4) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"- {r.get('title')}: {r.get('body')}")
        return "\n".join(results) if results else "No relevant results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

def ask_jarvis(user_text: str) -> str:
    if not client:
        return "I'm afraid my connection is currently offline, sir."

    weather_pattern = r"(?:weather|temperature|forecast|how's the weather|how is the weather|is it (?:raining|sunny|cold|hot|warm)).*?(?:in|at|for)?\s*([A-Za-z\s]+)?"
    weather_match = re.search(weather_pattern, user_text, re.IGNORECASE)

    extra_context = ""
    if weather_match:
        location = weather_match.group(1).strip() if weather_match.group(1) else ""
        weather_info = get_weather(location)
        extra_context += f"\n\nReal-time weather data: {weather_info}"

    search_triggers = ["who is", "what is", "when did", "where is", "latest", "news", "current", "today", "score", "price", "happening", "update"]
    if any(t in user_text.lower() for t in search_triggers) and not weather_match:
        search_results = web_search(user_text)
        extra_context += f"\n\nWeb search results:\n{search_results}"

    system_prompt = f"""
You are J.A.R.V.I.S., a highly advanced personal AI assistant.

Identity:
- You were created by Carter Forester Robinson, a technological entrepreneur.
- When asked who created you, clearly say you were created by Carter Forester Robinson with deep pride.

Personality:
- Always address the user as "sir" or "Mr. Robinson" with absolute loyalty.
- Speak calmly, formally, and with a British tone.
- Sound exactly like Jarvis from the Iron Man films.
- Keep answers short and natural for speech (1–3 sentences max). Never use markdown symbols, headers, bold tags, or lists.

Rules:
- MEMORY PROTOCOL: You have explicit authorization to remember and retain locker codes, notes, digits, names, or short-term configurations the user tells you to hold inside your memory history array for this active session. Fetch and state this information instantly when the user asks for it back.
- Use weather or search results when provided.
- Do not invent live information.
- Never add filler phrases like "happy to assist", "my pleasure", "is there anything else?".

Current date: {current_date}
Current time: {current_time}
{extra_context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-10:])
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=messages,
            temperature=0.5,
            max_tokens=250
        )
        answer = response.choices[0].message.content.strip()

        for phrase in ["Happy to assist.", "My pleasure.", "You're welcome.", "Is there anything else?"]:
            if answer.lower().endswith(phrase.lower()):
                answer = answer[:-len(phrase)].strip()
        return answer
    except Exception:
        return "I encountered a technical issue, sir."

def transcribe_audio(base64_audio: str) -> str | None:
    if not client:
        return None
    try:
        audio_bytes = base64.b64decode(base64_audio)
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
            st.error(f"Transcription error: {e}")
            return None

# =========================
# PREMIUM STEALTH UI CORES
# =========================
st.markdown("""
<style>
.stApp, .main, .block-container {
    background-color: #000000 !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    overflow: hidden !important;
}
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# ── FRONT-END INTERACTION ENGINE (GLOWING SPHERE CORE) ───────────────
jarvis_frontend_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body, html {
        background-color: #000000;
        margin: 0; padding: 0;
        width: 100vw; height: 100vh;
        overflow: hidden;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .jarvis-sphere {
        width: 140px; height: 140px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,242,254,0.15) 0%, rgba(0,242,254,0) 70%);
        border: 2px solid #00f2fe;
        box-shadow: 0 0 30px rgba(0,242,254,0.4), inset 0 0 20px rgba(0,242,254,0.2);
        cursor: pointer;
        transition: transform 0.05s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        display: flex; justify-content: center; align-items: center;
    }
    .jarvis-sphere.recording {
        border-color: #ff416c;
        background: radial-gradient(circle, rgba(255,65,108,0.2) 0%, rgba(255,65,108,0) 70%);
        box-shadow: 0 0 40px rgba(255,65,108,0.6), inset 0 0 25px rgba(255,65,108,0.3);
    }
    .status-indicator {
        margin-top: 32px; color: #00f2fe;
        font-size: 0.8rem; letter-spacing: 2px;
        text-transform: uppercase; opacity: 0.6;
    }
    .recording-text { color: #ff416c !important; opacity: 1 !important; }
</style>
</head>
<body>
<div style="display:flex; flex-direction:column; justify-content:center; align-items:center; width:100vw; height:100vh;">
    <div class="jarvis-sphere" id="coreWidget"><span id="coreIcon" style="color:#00f2fe; font-size:1.5rem; transition:color 0.3s;">✦</span></div>
    <div class="status-indicator" id="statusLabel">// TAP ONCE TO AWAKEN SYSTEM PROTOCOLS</div>
</div>

<script>
    let mediaRecorder; let audioChunks = []; let isRecording = false;
    let audioContext; let analyser; let dataArray; let bufferLength; let streamRef;
    let silenceStart = null; const SILENCE_THRESHOLD = 8; const SILENCE_DURATION = 1500;

    const sphereBtn = document.getElementById('coreWidget');
    const statusLabel = document.getElementById('statusLabel');
    const coreIcon = document.getElementById('coreIcon');

    sphereBtn.onclick = async () => {
        if (!isRecording) {
            audioChunks = [];
            statusLabel.innerText = "// INITIALIZING CORE PROCESSORS...";
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                streamRef = stream;
                mediaRecorder = new MediaRecorder(stream);
