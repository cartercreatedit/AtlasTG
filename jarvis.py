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
# STYLING
# ========================
# =========================
# LAYOUT & INTERACTION (CINEMATIC COALITION CORE)
# =========================
st.markdown("""
<style>
    /* Force canvas environment to blend cleanly into a deep Stark lab background */
    .stApp { background: #030305; }
    iframe { width: 100% !important; margin: 0 auto; display: block; }
</style>
""", unsafe_allow_html=True)

# Main Title Headers matching the digital heads-up display tracking style
st.markdown("<h2 style='text-align: center; color: #ff5500; text-shadow: 0 0 20px rgba(255, 60, 0, 0.6); font-weight: 100; letter-spacing: 12px; font-family: monospace; font-size: 26px; margin-top: 10px;'>J.A.R.V.I.S.</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #cc4400; font-family: monospace; font-size: 11px; letter-spacing: 4px; margin-bottom: -10px; opacity: 0.75;'>AI MAINFRAME HOLOGRAPHIC GEOMETRY</p>", unsafe_allow_html=True)

# Injecting the scaled-up widescreen movie-accurate canvas simulation engine
st.components.v1.html("""
<div style="display: flex; justify-content: center; align-items: center; width: 100%; height: 500px; background: #030305; overflow: hidden;">
    <canvas id="movieJarvisCanvas" width="600" height="500"></canvas>
</div>
<script>
    const canvas = document.getElementById('movieJarvisCanvas');
    const ctx = canvas.getContext('2d');
    
    let time = 0;
    
    // Matrix tracking lines to populate the complex background wireframe grid from your image
    function drawGrid(cx, cy) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 60, 0, 0.04)';
        ctx.lineWidth = 1;
        // Radiating technical compass background ticks
        for (let a = 0; a < Math.PI * 2; a += Math.PI / 6) {
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + Math.cos(a) * 240, cy + Math.sin(a) * 240);
        }
        ctx.stroke();
    }

    function renderMovieCore() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        time += 0.015;
        
        let cx = canvas.width / 2;
        let cy = canvas.height / 2;
        
        // Render subtle radar grid layers first
        drawGrid(cx, cy);

        // 1. DENSE INNER CORE CORE ORB (The central engine glare from your picture)
        let coreRadius = 14 + Math.sin(time * 3) * 2;
        let coreGlow = ctx.createRadialGradient(cx, cy, 2, cx, cy, coreRadius * 1.8);
        coreGlow.addColorStop(0, 'rgba(255, 235, 180, 1)');
        coreGlow.addColorStop(0.3, 'rgba(255, 110, 0, 0.8)');
        coreGlow.addColorStop(1, 'rgba(255, 40, 0, 0)');
        
        ctx.beginPath();
        ctx.arc(cx, cy, coreRadius * 1.8, 0, Math.PI * 2);
        ctx.fillStyle = coreGlow;
        ctx.fill();

        // 2. RADIAL ENERGY SPIKES (The sharp laser strands reaching from center outwards)
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 130, 0, 0.25)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 24; i++) {
            let angle = (i / 24) * Math.PI * 2 + (time * 0.1);
            let offset = (i % 3 === 0) ? 190 : 130; // some long strands, some medium
            if (i % 5 === 0) {
                ctx.moveTo(cx + Math.cos(angle) * (coreRadius * 0.5), cy + Math.sin(angle) * (coreRadius * 0.5));
                ctx.lineTo(cx + Math.cos(angle) * offset, cy + Math.sin(angle) * offset);
            }
        }
        ctx.stroke();

        // 3. ASYMMETRICAL MOVIE SHIELD ARCS (The broken layered mechanical rings)
        // Layer A: Inner detailed tracking dial
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 90, 0, 0.6)';
        ctx.lineWidth = 2;
        ctx.arc(cx, cy, 45, time, time + Math.PI * 0.8);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.arc(cx, cy, 45, time + Math.PI, time + Math.PI * 1.4);
        ctx.stroke();

        // Layer B: Main intersecting technical structural shield line loop
        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(1.3, 0.75); // Warp geometry to match the tilted 3D oval look in your screenshot
        ctx.rotate(time * 0.3);
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 120, 0, 0.7)';
        ctx.lineWidth = 1.5;
        ctx.arc(0, 0, 95, 0, Math.PI * 1.5);
        ctx.stroke();
        
        // Add tiny block marker notes on the ring
        ctx.fillStyle = '#ff6a00';
        ctx.fillRect(Math.cos(0)*95 - 2, Math.sin(0)*95 - 2, 4, 4);
        ctx.fillRect(Math.cos(Math.PI*0.5)*95 - 2, Math.sin(Math.PI*0.5)*95 - 2, 4, 4);
        ctx.restore();

        // Layer C: Giant Outer Orbit Cage (The sprawling thin outer matrix shell)
        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(1.45, 0.9);
        ctx.rotate(-time * 0.15);
        
        // Draw the massive outer ring
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 60, 0, 0.35)';
        ctx.lineWidth = 1;
        ctx.arc(0, 0, 140, 0, Math.PI * 2);
        ctx.stroke();
        
        // Draw cross lines slicing directly through the ring shell
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 100, 0, 0.12)';
        for(let k=0; k<8; k++) {
            let a1 = (k/8)*Math.PI*2;
            let a2 = a1 + 0.4;
            ctx.moveTo(Math.cos(a1)*110, Math.sin(a1)*110);
            ctx.lineTo(Math.cos(a2)*140, Math.sin(a2)*140);
        }
        ctx.stroke();
        ctx.restore();

        // Layer D: The Dense Secondary Orbit Ring
        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(0.85, 1.35); // Vertical tilt variant matching movie schematics
        ctx.rotate(time * 0.25);
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 75, 0, 0.45)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 8]); // Dashed readouts
        ctx.arc(0, 0, 115, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();

        // 4. FLOATING CIRCUIT CLUSTER NODES (The random technical dots along vector endpoints)
        for (let j = 0; j < 12; j++) {
            let seedAngle = (j * 4.3) + (time * 0.05);
            let dist = 135 + Math.sin(time + j) * 8;
            let fx = cx + Math.cos(seedAngle) * dist;
            let fy = cy + Math.sin(seedAngle) * dist * 0.7;
            
            ctx.beginPath();
            ctx.arc(fx, fy, 2, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255, 150, 0, 0.75)';
            ctx.fill();
            
            // Draw a fine target connector tracking back down to center hub block
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(255, 80, 0, 0.07)';
            ctx.moveTo(fx, fy);
            ctx.lineTo(cx, cy);
            ctx.stroke();
        }

        requestAnimationFrame(renderMovieCore);
    }
    
    // Fire up the matrix calculations immediately on boot execution
    renderMovieCore();
</script>
""", height=510)

if "jarvis_original_output" in st.session_state and st.session_state.jarvis_original_output:
    raw_audio = st.session_state.jarvis_original_output
    st.session_state.jarvis_original_output = None
    
    with st.spinner("Processing audio matrix..."):
        text_input = transcribe_audio(raw_audio)
        if text_input:
            reply = ask_jarvis(text_input)
            st.session_state.speech_to_play = reply

component_data = {
    "active": True,
    "text_to_speak": st.session_state.speech_to_play
}

voice_component(data=component_data, key="jarvis_voice_module")
