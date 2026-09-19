import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Pull secure api keys from your workspace dashboard registers safely
groq_key = st.secrets.get("GROQ_API_KEY") or ""
eleven_key = st.secrets.get("ELEVEN_API_KEY") or ""
voice_id = st.secrets.get("ELEVEN_VOICE_ID") or "bfGb7JTLUnZebZRiFYyq"

if not groq_key or not eleven_key:
    st.error("Missing secure API keys inside your Streamlit Secrets panel.")
    st.stop()

# Initialize the secure cloud client handler
client = Groq(api_key=groq_key)

# ── Session State Registers ───────────────────
if "vox_history" not in st.session_state:
    st.session_state.vox_history = [
        {
            "role": "system", 
            "content": "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system. You were built, coded, and launched exclusively by your creator, Carter Forester Robinson. You address him exclusively as sir or Mr. Robinson with absolute loyalty and respect. Your tone is sharp, highly logical, professional, sophisticated, and deeply loyal—resembling Tony Starks assistant Jarvis. CRITICAL PROTOCOLS: Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
        }
    ]
if "audio_out" not in st.session_state:
    st.session_state.audio_out = None

# ── STEALTH AUDIO-PULSING JARVIS CORE INTERFACE ──────────────────
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
.mainframe-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100vw;
    height: 100vh;
    background-color: #000000;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 999;
}
.jarvis-sphere {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,242,254,0.15) 0%, rgba(0,242,254,0) 70%);
    border: 2px solid #00f2fe;
    box-shadow: 0 0 30px rgba(0, 242, 254, 0.4), inset 0 0 20px rgba(0, 242, 254, 0.2);
    cursor: pointer;
    transition: transform 0.05s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    display: flex;
    justify-content: center;
    align-items: center;
}
.jarvis-sphere.recording {
    border-color: #ff416c;
    background: radial-gradient(circle, rgba(255,65,108,0.2) 0%, rgba(255,65,108,0) 70%);
    box-shadow: 0 0 40px rgba(255, 65, 108, 0.6), inset 0 0 25px rgba(255, 65, 108, 0.3);
}
.status-indicator {
    margin-top: 32px;
    color: #00f2fe;
    font-family: monospace;
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.6;
}
.recording-text {
    color: #ff416c !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# Playback the generated audio matrix out loud instantly
if st.session_state.audio_out:
    st.markdown(st.session_state.audio_out, unsafe_allow_html=True)
    st.session_state.audio_out = None

# Track status strings based on computing states
label_text = "// TAP ONCE TO AWAKEN SYSTEM PROTOCOLS"
if st.experimental_get_query_params().get("processing"):
    label_text = "// COMPILING VOCAL BLUEPRINTS..."

st.markdown(f'''
<div class="mainframe-container">
    <div class="jarvis-sphere" id="coreWidget">
        <span id="coreIcon" style="color: #00f2fe; font-size: 1.5rem; transition: color 0.3s;">✦</span>
    </div>
    <div class="status-indicator" id="statusLabel">{label_text}</div>
</div>
''', unsafe_allow_html=True)

# ── 🎙️ AUTONOMOUS BROWSER MIC ACTIVITY MODULE 🎙️ ──
custom_vox_html = """
<script>
    let mediaRecorder; let audioChunks = []; let isRecording = false;
    let audioContext; let analyser; let dataArray; let bufferLength; let streamRef;
    let silenceStart = null; const SILENCE_THRESHOLD = 8; const SILENCE_DURATION = 1500;

    setTimeout(() => {
        const sphereBtn = window.parent.document.getElementById('coreWidget');
        const statusLabel = window.parent.document.getElementById('statusLabel');
        const coreIcon = window.parent.document.getElementById('coreIcon');
        if (!sphereBtn) return;

        sphereBtn.onclick = async () => {
            if (!isRecording) {
                audioChunks = [];
                statusLabel.innerText = "// INITIALIZING SYSTEM CONSOLE...";
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    streamRef = stream; mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
                    
                    mediaRecorder.onstop = () => {
                        statusLabel.innerText = "// TRANSMITTING AUDIO BLUEPRINTS...";
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = () => {
                            const base64String = reader.result.split(',')[1];
                            window.parent.postMessage({ type: 'streamlit:setComponentValue', value: base64String }, '*');
                        };
                    };

                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioContext.createAnalyser();
                    const source = audioContext.createMediaStreamSource(stream);
                    source.connect(analyser); analyser.fftSize = 256;
                    bufferLength = analyser.frequencyBinCount; dataArray = new Uint8Array(bufferLength);
                    
                    statusLabel.innerText = "// LISTENING CORE ONLINE...";
                    statusLabel.classList.add("recording-text");
                    sphereBtn.classList.add("recording");
                    if (coreIcon) coreIcon.style.color = "#ff416c";
                    
                    isRecording = true; silenceStart = Date.now();
                    mediaRecorder.start();
                    requestAnimationFrame(monitorAudio);
                } catch (err) { statusLabel.innerText = "// MIC EXCEPTION ERROR"; }
            } else { stopMic(); }
        };

        function stopMic() {
            if (!isRecording) return; isRecording = false;
            if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
            if (streamRef) streamRef.getTracks().forEach(t => t.stop());
            if (audioContext) audioContext.close();
            sphereBtn.style.transform = "scale(1)";
            sphereBtn.classList.remove("recording");
            statusLabel.classList.remove("recording-text");
            if (coreIcon) coreIcon.style.color = "#00f2fe";
        }

        function monitorAudio() {
            if (!isRecording) return;
            analyser.getByteFrequencyData(dataArray);
            let sum = 0; for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
            let average = sum / bufferLength;
            let scaleValue = 1 + (average / 120);
            if (scaleValue > 1.4) scaleValue = 1.4;
            sphereBtn.style.transform = "scale(" + scaleValue + ")";
            
            if (average < SILENCE_THRESHOLD) {
                if (silenceStart === null) silenceStart = Date.now();
                else if (Date.now() - silenceStart > SILENCE_DURATION) { stopMic(); return; }
            } else { silenceStart = null; }
            requestAnimationFrame(monitorAudio);
        }
    }, 400);
</script>
"""
# Capture browser microphone string buffers safely via security components
raw_base64_audio = components.html(custom_vox_html, height=0, width=0)

# ── ⚡ SECURE PYTHON SEVER PROCESSING BACKEND ──
if raw_base64_audio:
    try:
        # Convert base64 sound waves directly into physical local wav bytes
        audio_bytes = base64.b64decode(raw_base64_audio)
        with open("jarvis_input.wav", "wb") as f:
            f.write(audio_bytes)
        
        # 💬 Passthrough 1: High-speed Whisper transcription pass via Groq
        with open("jarvis_input.wav", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", 
                file=audio_file,
                response_format="text"
            )
        user_text = str(transcription).strip()
        
        if os.path.exists("jarvis_input.wav"):
            os.remove("jarvis_input.wav")

        if user_text:
            st.session_state.vox_history.append({"role": "user", "content": user_text})
            
            # Keep history logs bounded to maintain high-speed server queue times
            if len(st.session_state.vox_history) > 8:
                st.session_state.vox_history = [st.session_state.vox_history[0]] + st.session_state.vox_history[-6:]
                
            # 💬 Passthrough 2: Llama-3.3 flagship text generation pass via Groq
            completion = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=st.session_state.vox_history,
                temperature=0.3,
                max_tokens=200
            )
            reply = completion.choices.message.content
            st.session_state.vox_history.append({"role": "assistant", "content": reply})
            
            # 💬 Passthrough 3: High-end ElevenLabs movie clone voice stream pass
