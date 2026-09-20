import streamlit as st
from groq import Groq
import datetime
import base64

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
    const {
        parentElement,
        data,
        setTriggerValue
    } = component;

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

    // Force load voices
    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
    }

    // =========================
    // START MICROPHONE
    // =========================
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

            recorder = new MediaRecorder(stream, {
                mimeType: "audio/webm"
            });

            const chunks = [];

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            };

            recorder.onstop = async () => {
                listening = false;
                if (animationFrame) cancelAnimationFrame(animationFrame);
                if (stream) stream.getTracks().forEach(track => track.stop());

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
                        if (recorder && recorder.state === "recording") {
                            recorder.stop();
                        }
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

    // =========================
    // SPEAK RESPONSE (Jarvis-like)
    // =========================
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

        const preferred = [
            "Google UK English Male",
            "Microsoft George - English (United Kingdom)",
            "Microsoft David - English (United States)",
            "Daniel",
            "Alex",
            "Google US English"
        ];

        let selectedVoice = null;
        for (const name of preferred) {
            selectedVoice = voices.find(v => v.name.includes(name));
            if (selectedVoice) break;
        }

        if (!selectedVoice) {
            selectedVoice = voices.find(v =>
                v.lang.startsWith("en-GB") && v.name.toLowerCase().includes("male")
            );
        }

        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith("en"));
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        utterance.rate = 0.92;
        utterance.pitch = 0.85;
        utterance.volume = 1.0;

        utterance.onend = () => {
            speaking = false;
            setTimeout(startListening, 250);
        };

        utterance.onerror = () => {
            speaking = false;
            setTimeout(startListening, 250);
        };

        window.speechSynthesis.speak(utterance);
    }

    // =========================
    // PYTHON → JAVASCRIPT
    // =========================
    if (data && data.speak && data.speak !== lastSpeech) {
        lastSpeech = data.speak;
        speak(data.speak);
    }

    // =========================
    // START WHEN ACTIVATED
    // =========================
    if (data && data.active === true && !listening && !speaking) {
        setTimeout(startListening, 100);
    }

    // =========================
    // CLEANUP
    // =========================
    return () => {
        if (animationFrame) cancelAnimationFrame(animationFrame);
        if (stream) stream.getTracks().forEach(track => track.stop());
        if (audioContext) audioContext.close();
    };
}
"""
)

# =========================
# AI
# =========================
def ask_jarvis(user_text):
    if not client:
        return "My Groq API key isn't connected."

    system_prompt = f"""
You are J.A.R.V.I.S., Tony Stark's personal AI assistant.
Current date: {current_date}
Current time: {current_time}

Speak naturally, calmly and with a slight British tone in your wording.
Keep responses short and conversational because they will be spoken aloud.
Reply in the same language the user uses.
Do not use markdown or bullet points.
Never invent real-time data (weather, news, stock prices, etc.).
If the user asks for live information you cannot access, politely say you don't have access to that data right now.
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-10:])
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content
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
    .stApp {
        background: #0a0a0a;
    }
    .main-circle {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #1a1a2e, #0f0f1a);
        border: 3px solid #00d4ff;
        box-shadow: 0 0 40px rgba(0, 212, 255, 0.4),
                    inset 0 0 20px rgba(0, 212, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 80px auto 20px auto;
        cursor: pointer;
        transition: all 0.3s ease;
        user-select: none;
    }
    .main-circle:hover {
        box-shadow: 0 0 60px rgba(0, 212, 255, 0.7),
                    inset 0 0 30px rgba(0, 212, 255, 0.2);
        transform: scale(1.05);
    }
    .main-circle.active {
        border-color: #00ff9d;
        box-shadow: 0 0 50px rgba(0, 255, 157, 0.6),
                    inset 0 0 25px rgba(0, 255, 157, 0.15);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 40px rgba(0, 255, 157, 0.5); }
        50% { box-shadow: 0 0 70px rgba(0, 255, 157, 0.8); }
        100% { box-shadow: 0 0 40px rgba(0, 255, 157, 0.5); }
    }
    .circle-text {
        color: #00d4ff;
        font-size: 18px;
        font-weight: 500;
        letter-spacing: 2px;
        text-align: center;
    }
    .active .circle-text {
        color: #00ff9d;
    }
    .status-text {
        text-align: center;
        color: #666;
        font-size: 14px;
        margin-top: 10px;
        letter-spacing: 1px;
    }
    .title {
        text-align: center;
        color: #00d4ff;
        font-size: 28px;
        letter-spacing: 8px;
        margin-top: 40px;
        font-weight: 300;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.markdown('<div class="title">J.A.R.V.I.S.</div>', unsafe_allow_html=True)

# =========================
# CIRCLE BUTTON
# =========================
circle_class = "main-circle active" if st.session_state.voice_active else "main-circle"
label = "LISTENING" if st.session_state.voice_active else "START"

# We use a normal Streamlit button but style it to look like the circle is clickable
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button(label, key="circle_btn", use_container_width=True):
        st.session_state.voice_active = not st.session_state.voice_active
        if not st.session_state.voice_active:
            st.session_state.speech_to_play = ""
        st.rerun()

# Visual circle (purely decorative)
st.markdown(f"""
<div class="{circle_class}">
    <div class="circle-text">{label}</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.voice_active:
    st.markdown('<div class="status-text">VOICE SYSTEM ACTIVE</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-text">CLICK THE CIRCLE TO START</div>', unsafe_allow_html=True)

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
