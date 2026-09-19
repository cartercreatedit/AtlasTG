import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
import io
import streamlit.components.v1 as components
import requests

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
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

# ── API Key Configuration ─────────────────────
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
eleven_api_key = st.secrets.get("ELEVEN_API_KEY") or os.getenv("ELEVEN_API_KEY")
eleven_voice_id = st.secrets.get("ELEVEN_VOICE_ID") or os.getenv("ELEVEN_VOICE_ID")

if not groq_api_key or not eleven_api_key or not eleven_voice_id:
    st.error("Missing secure configuration tokens inside Secrets registers.")
    st.stop()

client = Groq(api_key=groq_api_key)

# ── Session State Registers ───────────────────
if "vox_history" not in st.session_state:
    st.session_state.vox_history = []
if "incoming_bytes" not in st.session_state:
    st.session_state.incoming_bytes = None
if "audio_playback_tag" not in st.session_state:
    st.session_state.audio_playback_tag = None

if st.session_state.audio_playback_tag:
    st.markdown(st.session_state.audio_playback_tag, unsafe_allow_html=True)
    st.session_state.audio_playback_tag = None 

# ── THE VOX CORE MAINFRAME DISPLAY GRAPHIC ───────────────────
is_active_recording = st.session_state.incoming_bytes is not None

st.markdown(f'''
<div class="mainframe-container">
    <div class="jarvis-sphere {"recording" if is_active_recording else ""}" id="coreWidget">
        <span style="color: {"#ff416c" if is_active_recording else "#00f2fe"}; font-size: 1.5rem;" id="coreIcon">✦</span>
    </div>
    <div class="status-indicator" id="statusLabel">
        // TAP CORE ONCE TO START TALKING, SIR
    </div>
</div>
''', unsafe_allow_html=True)

# ── 🎙️ AUTOMATED SILENCE-SENSING MIC DRIVER (Hands-Free Upgrade) 🎙️ ──
custom_vox_html = """
<script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let audioContext;
    let analyser;
    let streamReference;
    let silenceTimeout = null;

    setTimeout(() => {
        const sphereBtn = window.parent.document.getElementById('coreWidget');
        const statusLabel = window.parent.document.getElementById('statusLabel');
        const coreIcon = window.parent.document.getElementById('coreIcon');
        if (!sphereBtn) return;

        sphereBtn.onclick = async () => {
            if (isRecording) return; // Prevent double tap bugs completely
            
            audioChunks = [];
            statusLabel.innerText = "// STARTING HANDS-FREE CORE...";
            
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamReference = stream;
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) audioChunks.push(e.data);
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64String = reader.result.split(',');
                    window.parent.postMessage({ type: 'streamlit:setComponentValue', value: base64String }, '*');
                };
                stream.getTracks().forEach(track => track.stop());
            };

            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            statusLabel.innerText = "// SPEAK FREELY, SIR. CORE IS LISTENING...";
            statusLabel.classList.add("recording-text");
            sphereBtn.classList.add("recording");
            if(coreIcon) { coreIcon.style.color = "#ff416c"; }
            isRecording = true;

            function checkAudioSilence() {
                if (!isRecording) return;
                
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                let average = sum / bufferLength;
                
                // Real-time responsive visual enlarger scales perfectly to your voice level
                let scaleValue = 1 + (average / 130); 
                if (scaleValue > 1.4) scaleValue = 1.4; 
                sphereBtn.style.transform = "scale(" + scaleValue + ")";

                // ── INTELLIGENT AUTO-STOP PROTOCOL ──
                if (average < 7) { // Audio threshold drop registers silence
                    if (!silenceTimeout) {
                        silenceTimeout = setTimeout(() => {
                            statusLabel.innerText = "// SILENCE DETECTED. TRANSMITTING...";
                            isRecording = false;
                            sphereBtn.style.transform = "scale(1)";
                            sphereBtn.classList.remove("recording");
                            statusLabel.classList.remove("recording-text");
                            if(coreIcon) { coreIcon.style.color = "#00f2fe"; }
                            
                            if (mediaRecorder && mediaRecorder.state === "recording") {
                                mediaRecorder.stop();
                            }
                            if (streamReference) {
                                streamReference.getTracks().forEach(track => track.stop());
                            }
                            if (audioContext) {
                                audioContext.close();
                            }
                        }, 1500); // Triggers automatically after exactly 1.5 seconds of quiet breathing
                    }
                } else {
                    // Instantly clears the countdown timer the moment you make a sound
                    clearTimeout(silenceTimeout);
                    silenceTimeout = null;
                }

                requestAnimationFrame(checkAudioSilence);
            }

            mediaRecorder.start();
            requestAnimationFrame(checkAudioSilence);
        };
    }, 400);
</script>
"""
raw_mic_stream = components.html(custom_vox_html, height=0, width=0)

# ── PROCESS INCOMING AUDIO MATRIX FREQUENCIES ────────────────
if raw_mic_stream and raw_mic_stream != st.session_state.incoming_bytes:
    st.session_state.incoming_bytes = raw_mic_stream
    
    try:
        audio_data_bytes = base64.b64decode(raw_mic_stream)
        with open("jarvis_temp_input.wav", "wb") as f:
            f.write(audio_data_bytes)
        
        with open("jarvis_temp_input.wav", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", 
                file=audio_file,
                response_format="text"
            )
        
        user_spoken_prompt = str(transcription).strip()
        if os.path.exists("jarvis_temp_input.wav"):
            os.remove("jarvis_temp_input.wav")

        if user_spoken_prompt:
            st.session_state.vox_history.append({"role": "user", "content": user_spoken_prompt})
            
            sys_content = "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system built by Carter Forester Robinson in an intensive sprint on September 18, 2026. You address him exclusively as 'sir' or 'Mr. Robinson' with absolute loyalty. Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
            api_messages = [{"role": "system", "content": sys_content}]
            
            for m in st.session_state.vox_history[-6:]:
                if isinstance(m["content"], list):
