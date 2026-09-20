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
        answer = response.choices[0].message.content.strip()

        for phrase in ["Happy to assist.", "My pleasure.", "You're welcome.", "Is there anything else?"]:
            if answer.lower().endswith(phrase.lower()):
                answer = answer[:-len(phrase)].strip()

        # Added Memory Tracking Lines Below:
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

                const reader = new FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    setTriggerValue({ type: 'audio', data: base64data });
                };
            };

            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);

            recorder.start();
            listening = true;
            speechStarted = false;
            silenceStart = null;

            checkAudio();
        } catch (err) {
            console.error("Audio recording failed:", err);
            setTriggerValue({ type: 'error', error: err.message });
        }
    }

    function checkAudio() {
        if (!listening) return;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        const average = sum / dataArray.length / 255;

        const now = Date.now();

        if (average > SPEECH_THRESHOLD) {
            if (!speechStarted) {
                speechStarted = true;
                speechStartTime = now;
            }
            silenceStart = null;
        } else {
            if (speechStarted) {
                if (!silenceStart) {
