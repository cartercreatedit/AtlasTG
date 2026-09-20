import streamlit as st
from groq import Groq
import datetime
import base64
import requests
import re
from duckduckgo_search import DDGS

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
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False
if "speech_to_play" not in st.session_state:
    st.session_state.speech_to_play = ""
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

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

    # Custom Easter Eggs & Memory Wipes
    if "initiate self-destruction" in user_text.lower() or "clear out the lab" in user_text.lower():
        return "Very well, sir. Self-destruction sequence initiated. Five. Four. Three. Two. One. ... Just kidding, sir. Should I alert the local fire department, or do you intend to survive this one?"

    if "clean slate" in user_text.lower():
        st.session_state.messages = []
        return "Understood, sir. Clearing the session history logs. We have a fresh slate."

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
        answer = response.choices.message.content.strip()

        for phrase in ["Happy to assist.", "My pleasure.", "You're welcome.", "Is there anything else?"]:
            if answer.lower().endswith(phrase.lower()):
                answer = answer[:-len(phrase)].strip()

        # Update core conversation logs for memory
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.session_state.messages.append({"role": "assistant", "content": answer})

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
    search_triggers = ["who is", "what is", "when did", "where is", "latest", "news", "current", "today", "score", "price", "happening", "update"]
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
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.session_state.messages.append({"role": "assistant", "content": answer})

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
# VOICE COMPONENT (Original style)
# =========================
voice_component = st.components.v2.component(
    name="jarvis_original",
    html="",
    css="#voice-ui { width: 100%; height: 1px; overflow: hidden; }",
    js="""
export default function(component) {
    const { data, setTriggerValue } = component;

    let stream = null;
    let recorder = null;
    let audioContext = null;
    let analyser = null;
    let animationFrame = null;
    let listening = false;
    let speechStarted = false;
    let silenceStart = null;
    let lastSpeech = "";
    let speaking = false;
    let speechStartTime = null;

    const SPEECH_THRESHOLD = 0.013;
    const SILENCE_TIME = 1600;
    const MIN_SPEECH_TIME = 400;

    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
    }

    function getSupportedMimeType() {
        const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
        for (const t of types) {
            if (window.MediaRecorder && MediaRecorder.isTypeSupported(t)) return t;
        }
        return "";
    }

    async function startListening() {
        if (listening || speaking) return;

        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
            });

            const mimeType = getSupportedMimeType();
            recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
            const chunks = [];

            recorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunks.push(e.data);
            };

            recorder.onstop = async () => {
                listening = false;
                if (animationFrame) cancelAnimationFrame(animationFrame);
                if (stream) stream.getTracks().forEach(t => t.stop());

                if (chunks.length === 0) {
                    setTimeout(startListening, 500);
                    return;
                }

                const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
                if (blob.size < 700) {
                    setTimeout(startListening, 500);
                    return;
                }

                const buffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(buffer);
                let binary = "";
                for (let i = 0; i < bytes.length; i += 8192) {
                    binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + 8192, bytes.length)));
                }
                setTriggerValue("audio", btoa(binary));
            };

            recorder.start(300);
            listening = true;
            speechStarted = false;
            silenceStart = null;
            speechStartTime = null;

            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            const dataArray = new Uint8Array(analyser.fftSize);

            function detect() {
                if (!listening) return;
                analyser.getByteTimeDomainData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    const v = (dataArray[i] - 128) / 128;
                    sum += v * v;
                }
                const rms = Math.sqrt(sum / dataArray.length);
                const now = Date.now();

                if (rms > SPEECH_THRESHOLD) {
                    if (!speechStarted) {
                        speechStarted = true;
                        speechStartTime = now;
                    }
                    silenceStart = null;
                } else if (speechStarted) {
                    if (!silenceStart) silenceStart = now;
                    if ((now - speechStartTime) >= MIN_SPEECH_TIME && (now - silenceStart) >= SILENCE_TIME) {
                        if (recorder && recorder.state === "recording") recorder.stop();
                        return;
                    }
                }
                animationFrame = requestAnimationFrame(detect);
            }
            detect();
        } catch (err) {
            setTriggerValue("error", String(err));
        }
    }

    function speak(text) {
        if (!text || speaking) return;
        if (!window.speechSynthesis) {
            setTimeout(startListening, 500);
            return;
        }

        speaking = true;
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        const voices = window.speechSynthesis.getVoices();

        const preferred = [
            "Google UK English Male",
            "Microsoft George - English (United Kingdom)",
            "Microsoft David - English (United States)",
            "Daniel",
            "Alex"
        ];

        let selected = null;
        for (const name of preferred) {
            selected = voices.find(v => v.name.includes(name));
            if (selected) break;
        }
        if (!selected) selected = voices.find(v => v.lang && v.lang.startsWith("en-GB"));
        if (!selected) selected = voices.find(v => v.lang && v.lang.startsWith("en"));
        if (selected) utterance.voice = selected;

        utterance.rate = 0.88;
        utterance.pitch = 0.80;
        utterance.volume = 1.0;

        utterance.onend = () => {
            speaking = false;
            setTimeout(startListening, 600);
        };
        utterance.onerror = () => {
            speaking = false;
            setTimeout(startListening, 600);
        };

        window.speechSynthesis.speak(utterance);
    }

    if (data && data.speak && data.speak !== lastSpeech && data.speak.length > 2) {
        lastSpeech = data.speak;
        speak(data.speak);
    }

    if (data && data.active === true && !listening && !speaking) {
        setTimeout(startListening, 200);
    }

    return () => {
        if (animationFrame) cancelAnimationFrame(animationFrame);
        if (stream) stream.getTracks().forEach(t => t.stop());
        if (audioContext) audioContext.close();
        window.speechSynthesis.cancel();
    };
}
"""
)

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
        margin: 40px 0 10px 0;
        font-weight: 200;
    }
    .main-circle {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #111827, #030712);
        border: 2px solid #00d4ff;
        box-shadow: 0 0 40px rgba(0, 212, 255, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 30px auto 10px auto;
    }
    .main-circle.active {
        border-color: #00ff9d;
        box-shadow: 0 0 50px rgba(0, 255, 157, 0.5);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 30px rgba(0, 255, 157, 0.4); }
        50% { box-shadow: 0 0 60px rgba(0, 255, 157, 0.7); }
        100% { box-shadow: 0 0 30px rgba(0, 255, 157, 0.4); }
    }
    .circle-text {
        color: #00d4ff;
        font-size: 15px;
        letter-spacing: 2px;
    }
    .active .circle-text { color: #00ff9d; }
    .status {
        text-align: center;
        color: #666;
        font-size: 13px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# UI
# =========================
st.markdown('<div class="title">J.A.R.V.I.S.</div>', unsafe_allow_html=True)

circle_class = "main-circle active" if st.session_state.voice_active else "main-circle"
label = "LISTENING" if st.session_state.voice_active else "START"

col1, col2, col3 = st.columns([1, 1.3, 1])
with col2:
    if st.button(label, key="btn", use_container_width=True):
        st.session_state.voice_active = not st.session_state.voice_active
        st.session_state.speech_to_play = ""
        st.rerun()

st.markdown(f'<div class="{circle_class}"><div class="circle-text">{label}</div></div>', unsafe_allow_html=True)

if st.session_state.voice_active:
    st.markdown('<div class="status">VOICE SYSTEM ACTIVE • SPEAK NOW</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status">CLICK TO ACTIVATE</div>', unsafe_allow_html=True)

# =========================
# COMPONENT
# =========================
component_data = {
    "active": st.session_state.voice_active,
    "speak": st.session_state.speech_to_play
}

result = voice_component(
    key="jarvis_comp",
    data=component_data,
    on_audio_change=lambda: None,
    on_error_change=lambda: None,
)

# =========================
# HANDLE AUDIO
# =========================
audio_data = getattr(result, "audio", None)

if audio_data and st.session_state.voice_active:
    spoken = transcribe_audio(audio_data)

    if spoken and spoken != st.session_state.last_spoken:
        st.session_state.last_spoken = spoken
        st.session_state.messages.append({"role": "user", "content": spoken})

        answer = ask_jarvis(spoken)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        st.session_state.speech_to_play = answer
        st.rerun()

error = getattr(result, "error", None)
if error:
    st.error(f"Mic error: {error}")
