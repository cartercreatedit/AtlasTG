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

        // Small delay so the previous speech fully stops
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
                // Only restart listening after speech is completely finished
                setTimeout(startListening, 700);
            };

            utterance.onerror = () => {
                speaking = false;
                setTimeout(startListening, 700);
            };

            window.speechSynthesis.speak(utterance);
        }, 150);
    }

    // Only speak if this is new text
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

    weather_match = re.search(
        r"(?:weather|temperature|forecast|how's the weather|how is the weather|is it 
