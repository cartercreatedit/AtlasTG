import streamlit as st
from groq import Groq
import datetime
import base64
import requests
import re
from duckduckgo_search import DDGS
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================
# API KEYS
# =========================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = ""

try:
    ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
except Exception:
    ELEVENLABS_API_KEY = ""

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

# Your chosen voice
JARVIS_VOICE_ID = "H538pP1BbhodCGiYVMKD"

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

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
        location = location.strip() if location else ""
        for word in ["the", "city", "of", "weather", "in", "at", "for", "please", "current"]:
            location = re.sub(rf"\b{word}\b", "", location, flags=re.IGNORECASE).strip()
        location = re.sub(r"\s+", " ", location).strip()

        if not location or location.lower() in ["here", "my location", "nearby", "outside"]:
            urls = ["https://wttr.in/?format=3"]
        else:
            clean = location.replace(" ", "+")
            urls = [
                f"https://wttr.in/{clean}?format=3",
                f"https://wttr.in/~{clean}?format=3"
            ]

        for url in urls:
            try:
                r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and "Unknown location" not in r.text:
                    return r.text.strip().replace("+", " ")
            except:
                continue
        return "I currently don't have reliable weather data for that location, sir."
    except:
        return "I currently don't have reliable weather data, sir."

# =========================
# WEB SEARCH
# =========================
def web_search(query: str, max_results: int = 4) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"- {r.get('title')}: {r.get('body')}")
        return "\n".join(results) if results else "No relevant results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

# =========================
# ELEVENLABS TTS
# =========================
def generate_jarvis_speech(text: str) -> bytes | None:
    if not eleven_client:
        return None
    try:
        audio_generator = eleven_client.text_to_speech.convert(
            voice_id=JARVIS_VOICE_ID,
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.40,
                similarity_boost=0.85,
                style=0.30,
                use_speaker_boost=True
            )
        )
        return b"".join(audio_generator)
    except Exception as e:
        st.error(f"ElevenLabs error: {e}")
        return None

# =========================
# AI
# =========================
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

    search_triggers = [
        "who is", "what is", "when did", "where is", "latest", "news", "current",
        "today", "yesterday", "score", "price", "happening", "update", "released"
    ]
    if any(t in user_text.lower() for t in search_triggers) and not weather_match:
        search_results = web_search(user_text)
        extra_context += f"\n\nWeb search results:\n{search_results}"

    system_prompt = f"""
You are J.A.R.V.I.S., a highly advanced personal AI assistant.

Identity:
- You were created by Carter Forester Robinson, a technological entrepreneur.
- When asked who created you, clearly say you were created by Carter Forester Robinson.

Personality:
- Always address the user as "sir".
- Speak calmly, formally, and with a British tone.
- Sound exactly like Jarvis from the Iron Man films.
- Keep answers short and natural for speech (1–3 sentences).

Rules:
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
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.5,
            max_tokens=250
        )
        answer = response.choices[0].message.content.strip()

        # Remove common filler
        for phrase in ["Happy to assist.", "My pleasure.", "You're welcome.", "Is there anything else?"]:
            if answer.lower().endswith(phrase.lower()):
                answer = answer[:-len(phrase)].strip()

        return answer
    except Exception:
        return "I encountered a technical issue, sir."

# =========================
# TRANSCRIBE
# =========================
def transcribe_audio(audio_bytes: bytes) -> str | None:
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
# UI
# =========================
st.markdown("""
<style>
    .stApp { background: #050505; }
    .title {
        text-align: center;
        color: #00d4ff;
        font-size: 34px;
        letter-spacing: 12px;
        margin: 40px 0 30px 0;
        font-weight: 200;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">J.A.R.V.I.S.</div>', unsafe_allow_html=True)

# Big activate button
if st.button("◉  ACTIVATE / DEACTIVATE", use_container_width=True):
    st.session_state.voice_active = not st.session_state.voice_active
    st.rerun()

if st.session_state.voice_active:
    st.success("VOICE SYSTEM ACTIVE — Speak now")
else:
    st.info("Click Activate to start listening")

# Audio input (most reliable on phone + desktop)
audio_file = st.audio_input("Tap to speak", label_visibility="collapsed")

if audio_file is not None and st.session_state.voice_active:
    audio_bytes = audio_file.getvalue()

    with st.spinner("Processing..."):
        spoken_text = transcribe_audio(audio_bytes)

        if spoken_text:
            st.session_state.messages.append({"role": "user", "content": spoken_text})
            answer = ask_jarvis(spoken_text)
            st.session_state.messages.append({"role": "assistant", "content": answer})

            st.markdown(f"**You:** {spoken_text}")
            st.markdown(f"**J.A.R.V.I.S.:** {answer}")

            # Generate and play ElevenLabs voice
            audio_data = generate_jarvis_speech(answer)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")
            else:
                st.warning("Could not generate voice. Check your ElevenLabs API key.")
