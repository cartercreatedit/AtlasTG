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
# VOICE COMPONENT
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

    const SPEECH_THRESHOLD = 0.013;
    const SILENCE_TIME = 1700;
    const MIN_SPEECH_TIME = 450;
    let speechStartTime = null;

    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
    }

    function getSupportedMimeType() {
        const types = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/mp4",
            "audio/aac",
            "audio/ogg;codecs=opus",
            "audio/ogg"
        ];
        for (const type of types) {
            if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return "";
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

            const mimeType = getSupportedMimeType();
            const options = mimeType ? { mimeType } : {};
            recorder = new MediaRecorder(stream, options);
            const chunks = [];

            recorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunks.push(e.data);
            };

            recorder.onstop = async () => {
                listening = false;
                if (animationFrame) cancelAnimationFrame(animationFrame);
                if (stream) stream.getTracks().forEach(t => t.stop());

                if (chunks.length === 0) {
                    setTimeout(startListening, 600);
                    return;
                }

                const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
                if (blob.size < 700) {
                    setTimeout(startListening, 600);
                    return;
                }

                const buffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(buffer);
                let binary = "";
                const chunkSize = 8192;
                for (let i = 0; i < bytes.length; i += chunkSize) {
                    binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + chunkSize, bytes.length)));
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

            function detectSpeech() {
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
                animationFrame = requestAnimationFrame(detectSpeech);
            }
            detectSpeech();
        } catch (err) {
            setTriggerValue("error", String(err));
        }
    }

    function speak(text) {
        if (!text || speaking) return;

        if (!window.speechSynthesis) {
            setTimeout(startListening, 600);
            return;
        }

        speaking = true;
        window.speechSynthesis.cancel();

        setTimeout(() => {
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

            utterance.rate = 0.87;
            utterance.pitch = 0.78;
            utterance.volume = 1.0;

            utterance.onend = () => {
                speaking = false;
                setTimeout(startListening, 700);
            };

            utterance.onerror = () => {
                speaking = false;
                setTimeout(startListening, 700);
            };

            window.speechSynthesis.speak(utterance);
        }, 150);
    }

    if (data && data.speak && data.speak !== lastSpeech && data.speak.length > 3) {
        lastSpeech = data.speak;
        speak(data.speak);
    }

    if (data && data.active === true && !listening && !speaking) {
        setTimeout(startListening, 300);
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
# AI
# =========================
def ask_jarvis(user_text: str) -> str:
    if not client:
        return "I'm afraid my connection is currently offline, sir."

    # Fixed regex - kept on one line
    weather_pattern = r"(?:weather|temperature|forecast|how's the weather|how is the weather|is it (?:raining|sunny|cold|hot|warm)).*?(?:in|at|for)?\s*([A-Za-z\s]+)?"
    weather_match = re.search(weather_pattern, user_text, re.IGNORECASE)

    extra_context = ""
    if weather_match:
        location = weather_match.group(1).strip() if weather_match.group(1) else ""
        weather_info = get_weather(location)
        extra_context = f"\n\nReal-time weather information: {weather_info}\nUse this data accurately and naturally."

    system_prompt = f"""
You are J.A.R.V.I.S.

Strict rules:
- Always call the user "sir".
- Speak in a calm, formal, British manner.
- Keep answers short (1 to 3 sentences maximum).
- NEVER add polite filler at the end such as:
  "Happy to assist", "My pleasure", "You're welcome", "Is there anything else?", "How else may I help you?", etc.
- Just give the information cleanly and stop.
- Sound exactly like Jarvis from the Iron Man films.

Current date: {current_date}
Current time: {current_time}
{extra_context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-6:])
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.45,
            max_tokens=180
        )
        answer = response.choices[0].message.content.strip()

        # Aggressive cleanup of unwanted endings
        bad_endings = [
            "Happy to assist.",
            "Happy to assist, sir.",
            "My pleasure.",
            "My pleasure, sir.",
            "You're welcome.",
            "You're most welcome.",
            "Is there anything else?",
            "Is there anything else I can help you with?",
            "How else may I assist you?",
            "How else may I help you?",
            "Let me know if you need anything else.",
            "At your service."
        ]

        for phrase in bad_endings:
            if answer.lower().endswith(phrase.lower()):
                answer = answer[:-len(phrase)].strip()
            if phrase.lower() in answer.lower()[-60:]:
                answer = re.sub(re.escape(phrase), "", answer, flags=re.IGNORECASE).strip()

        answer = answer.rstrip(" ,.-")
        return answer
    except Exception as e:
        return "I encountered a technical issue, sir."

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
