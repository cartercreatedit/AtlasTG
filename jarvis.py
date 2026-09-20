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
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False
if "speech_to_play" not in st.session_state:
    st.session_state.speech_to_play = ""

# =========================
# CURRENT TIME
# =========================
now = datetime.datetime.now()
current_time = now.strftime("%I:%M %p")
current_date = now.strftime("%A, %B %d, %Y")

# =========================
# WEATHER HELPER
# =========================
def get_weather(location: str = "") -> str:
    try:
        if not location or location.lower() in ["here", "my location", "current"]:
            url = "https://wttr.in/?format=3"
        else:
            # Clean location
            loc = location.strip().replace(" ", "+")
            url = f"https://wttr.in/{loc}?format=3"
        
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.text.strip()
        return "I couldn't retrieve the weather right now."
    except Exception:
        return "I couldn't retrieve the weather right now."

# =========================
# CUSTOM VOICE COMPONENT
# =========================
voice_component = st.components.v2.component(
    name="jarvis_hands_free_voice",
    html="""
""",
    css="""
#voice-ui {
    width: 100%;
    height: 1px;
    overflow: hidden;
}
""",
    js="""
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;

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

    const SPEECH_THRESHOLD = 0.018;
    const SILENCE_TIME = 1200;
    const MIN_SPEECH_TIME = 350;
    let speechStartTime = null;

    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
    }

    async function startListening() {
        if (listening || speaking) return;

        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            const chunks = [];

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) chunks.push(event.data);
            };

            recorder.onstop = async () => {
                listening = false;
                if (animationFrame) cancelAnimationFrame(animationFrame);
                if (stream) stream.getTracks().forEach(t => t.stop());

                const blob = new Blob(chunks, { type: "audio/webm" });
                if (blob.size < 1000) {
                    setTimeout(startListening, 300);
                    return;
                }

                const buffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(buffer);
                let binary = "";
                const chunkSize = 8192;
                for (let i = 0; i < bytes.length; i += chunkSize) {
                    const chunk = bytes.subarray(i, Math.min(i + chunkSize, bytes.length));
                    binary += String.fromCharCode(...chunk);
                }
                const base64 = btoa(binary);
                setTriggerValue("audio", base64);
            };

            recorder.start();
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

            function detectSpeech() {
                if (!listening) return;
                analyser.getByteTimeDomainData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    const value = (dataArray[i] - 128) / 128;
                    sum += value * value;
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
                    const speechDuration = now - speechStartTime;
                    const silenceDuration = now - silenceStart;
                    if (speechDuration >= MIN_SPEECH_TIME && silenceDuration >= SILENCE_TIME) {
                        if (recorder && recorder.state === "recording") recorder.stop();
                        return;
                    }
                }
                animationFrame = requestAnimationFrame(detectSpeech);
            }
            detectSpeech();
        } catch (error) {
            setTriggerValue("error", String(error));
        }
    }

    function speak(text) {
        if (!text) {
            setTimeout(startListening, 300);
            return;
        }
        if (!("speechSynthesis" in window)) {
            setTimeout(startListening, 300);
            return;
        }

        speaking = true;
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        const voices = window.speechSynthesis.getVoices();

        // Prefer deeper / British / male voices
        const preferred = [
            "Google UK English Male",
            "Microsoft George - English (United Kingdom)",
            "Microsoft David - English (United States)",
            "Daniel",
            "Alex"
        ];

        let selectedVoice = null;
        for (const name of preferred) {
            selectedVoice = voices.find(v => v.name.includes(name));
            if (selectedVoice) break;
        }
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith("en-GB"));
        }
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith("en"));
        }
        if (selectedVoice) utterance.voice = selectedVoice;

        utterance.rate = 0.90;
        utterance.pitch = 0.82;
        utterance.volume = 1.0;

        utterance.onend = () => {
            speaking = false;
            setTimeout(startListening, 300);
        };
        utterance.onerror = () => {
            speaking = false;
            setTimeout(startListening, 300);
        };

        window.speechSynthesis.speak(utterance);
    }

    if (data && data.speak && data.speak !== lastSpeech) {
        lastSpeech = data.speak;
        speak(data.speak);
    }

    if (data && data.active === true && !listening && !speaking) {
        setTimeout(startListening, 100);
    }

    return () => {
        if (animationFrame) cancelAnimationFrame(animationFrame);
        if (stream) stream.getTracks().forEach(t => t.stop());
        if (audioContext) audioContext.close();
    };
}
"""
)

# =========================
# AI
# =========================
def ask_jarvis(user_text: str) -> str:
    if not client:
        return "My Groq API key isn't connected."

    # Detect weather questions
    weather_match = re.search(
        r"(?:weather|temperature|forecast|how(?:'s| is) it outside|is it (?:raining|sunny|cold|hot)).*?(?:in|at|for)?\s*([A-Za-z\s]+)?",
        user_text,
        re.IGNORECASE
    )

    extra_context = ""
    if weather_match:
        location = weather_match.group(1).strip() if weather_match.group(1) else ""
        weather_info = get_weather(location)
        extra_context = f"\n\nReal-time weather data: {weather_info}\nUse this exact information when answering."

    system_prompt = f"""
You are J.A.R.V.I.S., a highly capable personal AI assistant inspired by the one from Iron Man.

Current date: {current_date}
Current time: {current_time}

You have broad knowledge of the world, science, technology, history, culture, and current events up to your training data.
You speak in a calm, intelligent, slightly British, and helpful manner.
Keep spoken responses relatively concise (2-4 sentences is ideal) because they will be read aloud.
Reply in the same language the user is using.

When the user asks for weather, use the real-time weather data provided below if available.
Never invent live data. If you don't have it, say so honestly.
{extra_context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-8:])
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.65,
            max_tokens=280
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I encountered an error: {str(e)}"

# =========================
# TRANSCRIBE
# =========================
def transcribe_audio(base64_audio):
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
    .main-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #111827, #030712);
        border: 2px solid #00d4ff;
        box-shadow: 0 0 50px rgba(0, 212, 255, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 40px auto 15px auto;
        transition: all 0.35s ease;
        cursor: pointer;
    }
    .main-circle.active {
        border-color: #00ff9d;
        box-shadow: 0 0 60px rgba(0, 255, 157, 0.55);
        animation: pulse 2.2s infinite;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 40px rgba(0, 255, 157, 0.4); }
        50%  { box-shadow: 0 0 80px rgba(0, 255, 157, 0.7); }
        100% { box-shadow: 0 0 40px rgba(0, 255, 157, 0.4); }
    }
    .circle-text {
        color: #00d4ff;
        font-size: 16px;
        letter-spacing: 3px;
        font-weight: 500;
    }
    .active .circle-text { color: #00ff9d; }
    .status {
        text-align: center;
        color: #555;
        font-size: 13px;
        letter-spacing: 1.5px;
        margin-bottom: 40px;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# UI
# =========================
st.markdown('<div class="title">J.A.R.V.I.S.</div>', unsafe_allow_html=True)

circle_class = "main-circle active" if st.session_state.voice_active else "main-circle"
label = "LISTENING" if st.session_state.voice_active else "START"

col1, col2, col3 = st.columns([1, 1.4, 1])
with col2:
    if st.button(label, key="main_btn", use_container_width=True):
        st.session_state.voice_active = not st.session_state.voice_active
        if not st.session_state.voice_active:
            st.session_state.speech_to_play = ""
        st.rerun()

st.markdown(f'''
<div class="{circle_class}">
    <div class="circle-text">{label}</div>
</div>
''', unsafe_allow_html=True)

if st.session_state.voice_active:
    st.markdown('<div class="status">VOICE SYSTEM ACTIVE • SPEAK NOW</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status">CLICK TO ACTIVATE</div>', unsafe_allow_html=True)

# =========================
# VOICE COMPONENT
# =========================
component_data = {
    "active": st.session_state.voice_active,
    "speak": st.session_state.speech_to_play
}

voice_result = voice_component(
    key="jarvis_voice",
    data=component_data,
    on_audio_change=lambda: None,
    on_error_change=lambda: None,
)

# =========================
# RECEIVE AUDIO
# =========================
audio_data = getattr(voice_result, "audio", None)

if audio_data:
    st.session_state.voice_active = True
    spoken_text = transcribe_audio(audio_data)

    if spoken_text:
        st.session_state.messages.append({"role": "user", "content": spoken_text})
        answer = ask_jarvis(spoken_text)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.speech_to_play = answer
        st.rerun()

# =========================
# ERROR
# =========================
component_error = getattr(voice_result, "error", None)
if component_error:
    st.error(f"Microphone error: {component_error}")

# =========================
# CLEAR SPEECH FLAG
# =========================
if st.session_state.speech_to_play:
    st.session_state.speech_to_play = ""
