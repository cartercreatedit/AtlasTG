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
# CURRENT TIME (Adjusted for Western Australia UTC+8)
# =========================
import time
now = datetime.datetime.utcfromtimestamp(time.time() + (8 * 3600))
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
- Speak calmly, formally, with a witty, dry British tone—exactly like Jarvis from the Iron Man films.
- Keep answers short and natural for speech (1–3 sentences max).

Rules:
- When the user explicitly says "hey jarvis", respond exactly with: "Hello, Mr. Forester Robinson, how can I help you?"
- For all other statements, questions, or commands, respond normally and intelligently without repeating the greeting.
- You have unrestricted, live access to real-time information via your background search. Always use provided real-time data naturally if asked.
- Never add filler phrases like "happy to assist" or "is there anything else?".

Current date: {current_date}
Current time: {current_time}
{extra_context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-10:])
    messages.append({"role": "user", "content": user_text})
        
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
            max_tokens=250
        )
        answer = response.choices.message.content.strip()
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
# LAYOUT & INTERACTION (HYPER-DENSITY LARGE INTERACTIVE CORE)
# =========================
st.markdown("""
<style>
    /* Blends the entire dashboard canvas space into a dark Stark lab background */
    .stApp { background: #020204; }
    
    /* Center aligns the iframe matrix layout cleanly */
    iframe { width: 100% !important; margin: 0 auto; display: block; }
    
    /* Styles the physical Start Button to match Tony Stark's orange interface look */
    div.stButton > button {
        display: block;
        margin: 20px auto 10px auto !important;
        background: #020204 !important;
        color: #ff5500 !important;
        border: 2px solid #ff5500 !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-family: monospace !important;
        font-size: 14px !important;
        letter-spacing: 2px !important;
        font-weight: bold !important;
        box-shadow: 0 0 15px rgba(255, 85, 0, 0.2) !important;
        transition: all 0.3s ease !important;
        cursor: pointer;
    }
    div.stButton > button:hover {
        background: #ff5500 !important;
        color: #020204 !important;
        box-shadow: 0 0 25px rgba(255, 85, 0, 0.6) !important;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #ff5500; text-shadow: 0 0 30px rgba(255, 50, 0, 0.85); font-weight: 100; letter-spacing: 16px; font-family: monospace; font-size: 24px; margin-top: 10px;'>J.A.R.V.I.S.</h2>", unsafe_allow_html=True)

# 1. THE HIGH-VISIBILITY ACTIVATION BUTTON SYSTEM
if st.button("✦ INITIALIZE VOCAL MATRIX ✦", key="stark_manual_voice_trigger"):
    st.session_state.voice_active = not st.session_state.voice_active
    st.rerun()

# Main UI Status Display
if st.session_state.voice_active:
    status_text = "VOCAL MATRIX ENGAGED // CAPTURING AUDIO CUES..."
    status_color = "#ff6a00"
else:
    status_text = "SYSTEM STANDBY // CLICK BUTTON ABOVE TO INITIALIZE LINK"
    status_color = "#993300"

st.markdown(f"<p style='text-align: center; color: {status_color}; font-family: monospace; font-size: 11px; letter-spacing: 3px; margin-top: 5px; margin-bottom: -15px;'>{status_text}</p>", unsafe_allow_html=True)

# Pass active state as string variable to safely bypass f-string parser conflicts
is_active_str = "true" if st.session_state.voice_active else "false"

# 2. SCALED-UP 380-NODE EXTRA-LARGE CORE SIMULATION ENGINE
st.components.v1.html(f"""
<div style="display: flex; justify-content: center; align-items: center; width: 100%; height: 520px; background: #020204; overflow: hidden; position: relative;">
    <canvas id="denseNeuralCanvas" width="600" height="520"></canvas>
</div>
<script>
    const canvas = document.getElementById('denseNeuralCanvas');
    const ctx = canvas.getContext('2d');
    
    const numParticles = 380; 
    let particles = [];
    let time = 0;
    
    let isJarvisSpeaking = false;
    let isVoiceActive = {is_active_str};

    function initHyperSphere() {{
        particles = [];
        for (let i = 0; i < numParticles; i++) {{
            let u = Math.random();
            let v = Math.random();
            let theta = u * 2.0 * Math.PI;
            let phi = Math.acos(2.0 * v - 1.0);
            let radius = 210; 
            
            particles.push({{
                x: radius * Math.sin(phi) * Math.cos(theta),
                y: radius * Math.sin(phi) * Math.sin(theta),
                z: radius * Math.cos(phi),
                ox: theta,
                oy: phi,
                seed: Math.random() * 10
            }});
        }}
    }}

    function project3D(x, y, z) {{
        let scale = 380 / (380 + z);
        return {{
            x: canvas.width / 2 + x * scale,
            y: canvas.height / 2 + y * scale,
            scale: scale,
            zDepth: z
        }};
    }}

    initHyperSphere();

    function renderDenseGrid() {{
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        let speedMultiplier = isJarvisSpeaking ? 0.045 : (isVoiceActive ? 0.02 : 0.005);
        let waveSurge = isJarvisSpeaking ? 40 : (isVoiceActive ? 20 : 6);
        
        time += speedMultiplier;

        let rotY = time * 0.35;
        let rotX = time * 0.18;
        let cosY = Math.cos(rotY), sinY = Math.sin(rotY);
        let cosX = Math.cos(rotX), sinX = Math.sin(rotX);

        let projectedNodes = [];

        particles.forEach((pt) => {{
            let noise = Math.sin(pt.ox * 5 + time * 2.5) * Math.cos(pt.oy * 5 + time * 1.8) * waveSurge;
            let currentRadius = 205 + noise;

            let x1 = currentRadius * Math.sin(pt.oy) * Math.cos(pt.ox);
            let y1 = currentRadius * Math.sin(pt.oy) * Math.sin(pt.ox);
            let z1 = currentRadius * Math.cos(pt.oy);

            let x2 = x1 * cosY + z1 * sinY;
            let z2 = z1 * cosY - x1 * sinY;

            let y3 = y1 * cosX - z2 * sinX;
            let z3 = z2 * cosX + y1 * sinX;

            projectedNodes.push(project3D(x2, y3, z3));
        }});

        ctx.lineWidth = 0.45;
        for (let i = 0; i < projectedNodes.length; i++) {{
            let p1 = projectedNodes[i];
            let currentConnections = 0;
            let proximityLimit = isVoiceActive ? 85 : 65; 

            for (let j = i + 1; j < projectedNodes.length; j++) {{
                if (currentConnections > 5) break; 
                
                let p2 = projectedNodes[j];
                let dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);

                if (dist < proximityLimit) {{
                    currentConnections++;
                    let alphaBase = isVoiceActive ? 0.32 : 0.18;
                    let alpha = (1 - (dist / proximityLimit)) * alphaBase * p1.scale;
                    
                    ctx.strokeStyle = "rgba(255, 85, 0, " + alpha + ")";
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }}
            }}
        }}

        projectedNodes.forEach(p => {{
            let nodeAlpha = isJarvisSpeaking ? 0.95 * p.scale : (isVoiceActive ? 0.75 * p.scale : 0.4 * p.scale);
            let sizeRadius = isJarvisSpeaking ? 2.5 * p.scale : (isVoiceActive ? 1.8 * p.scale : 1.2 * p.scale);
            
            ctx.fillStyle = "rgba(255, 120, 0, " + nodeAlpha + ")";
            ctx.beginPath();
            ctx.arc(p.x, p.y, sizeRadius, 0, Math.PI * 2);
            ctx.fill();
        }});

        requestAnimationFrame(renderDenseGrid);
    }

    window.addEventListener('message', (e) => {{
        if (e.data && e.data.type === 'jarvis_audio_state') {{
            isJarvisSpeaking = e.data.speaking;
        }}
    }});

    renderDenseGrid();
</script>
""", height=530)

if "jarvis_original_output" in st.session_state and st.session_state.jarvis_original_output:
    raw_audio = st.session_state.jarvis_original_output
    st.session_state.jarvis_original_output = None
    
    with st.spinner("Processing audio matrix..."):
        text_input = transcribe_audio(raw_audio)
        if text_input:
            reply = ask_jarvis(text_input)
            st.session_state.speech_to_play = reply

# Tells the JavaScript code if a voice payload is playing out loud right now
is_speaking_flag = "true" if (st.session_state.speech_to_play != "") else "false"
st.components.v1.html(f"""
<script>
    window.parent.postMessage({{type: 'jarvis_audio_state', speaking: {is_speaking_flag}}}, '*');
</script>
""", height=1)

# Forces microphone active flag to directly track python session state
component_data = {
    "active": st.session_state.voice_active,
    "text_to_speak": st.session_state.speech_to_play
}

voice_component(data=component_data, key="jarvis_voice_module")
