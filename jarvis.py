import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── API Key Configuration ────────────────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY inside secrets panel.")
    st.stop()

client = Groq(api_key=api_key)

# ── Session State Registers ──────────────────────────────────────────
if "vox_history" not in st.session_state:
    st.session_state.vox_history = []
if "audio_response_script" not in st.session_state:
    st.session_state.audio_response_script = None

# Automatically execute voice synthesizer script when reply is ready
if st.session_state.audio_response_script:
    st.markdown(st.session_state.audio_response_script, unsafe_allow_html=True)
    st.session_state.audio_response_script = None 

# ── NAZ LOUIS EXACT INTERFACE STYLING ────────────────────────────────
st.markdown("""
<style>
/* Wipes out default streamlit system banners and layouts */
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

/* Completely hides the background communication bridge from view */
div[data-testid="stTextArea"] {
    display: none !important;
    visibility: hidden !important;
    height: 0px !important;
}

/* Naz's Glowing Dynamic Audio Matrix Sphere */
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

<div class="mainframe-container">
    <div class="jarvis-sphere" id="coreWidget">
        <span style="color: #00f2fe; font-size: 1.5rem; transition: color 0.3s;" id="coreIcon">✦</span>
    </div>
    <div class="status-indicator" id="statusLabel">
        // TAP CORE TO COMMUNICATE, SIR
    </div>
</div>
""", unsafe_allow_html=True)

# ── BACK-END COUPLING LINK ───────────────────────────────────────────
incoming_audio_bytes = st.text_area("audio_bridge_stream", key="audio_bridge_stream")

# ── NAZ'S VISUAL SPHERE ANIMATION DRIVER ─────────────────────────────
custom_vox_html = """
<script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let audioContext;
    let analyser;
    let dataArray;
    let bufferLength;

    setTimeout(() => {
        const sphereBtn = window.parent.document.getElementById('coreWidget');
        const statusLabel = window.parent.document.getElementById('statusLabel');
        const coreIcon = window.parent.document.getElementById('coreIcon');
        if (!sphereBtn) return;

        sphereBtn.onclick = async () => {
            if (!isRecording) {
                audioChunks = [];
                statusLabel.innerText = "// INITIALIZING CORE PROCESSORS...";
                
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = () => {
                    statusLabel.innerText = "// GENERATING RESPONSE CODES...";
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        const base64String = reader.result.split(',')[1];
                        
                        // Locks the data directly onto the secure Python memory tray
                        const parentDoc = window.parent.document;
                        const textTrays = parentDoc.querySelectorAll('textarea[data-testid="stTextAreaRootElement"]');
                        if (textTrays.length > 0) {
                            textTrays[0].value = base64String;
                            const stateEvent = new Event('input', { bubbles: true });
                            textTrays[0].dispatchEvent(stateEvent);
                        }
                    };
                    stream.getTracks().forEach(track => track.stop());
                };

                // Real-time voice frequency scale driver
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                const source = audioContext.createMediaStreamSource(stream);
                source.connect(analyser);
                analyser.fftSize = 256;
                bufferLength = analyser.frequencyBinCount;
                dataArray = new Uint8Array(bufferLength);

                statusLabel.innerText = "// LISTENING CORE ONLINE...";
                statusLabel.classList.add("recording-text");
                sphereBtn.classList.add("recording");
                if(coreIcon) { coreIcon.style.color = "#ff416c"; }
                
                function animateNazSphere() {
                    if (!isRecording) {
                        sphereBtn.style.transform = "scale(1)";
                        return;
                    }
                    analyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
                    let average = sum / bufferLength;
                    let scaleValue = 1 + (average / 120);
                    if (scaleValue > 1.4) scaleValue = 1.4;
                    sphereBtn.style.transform = "scale(" + scaleValue + ")";
                    requestAnimationFrame(animateNazSphere);
                }

                mediaRecorder.start();
                isRecording = true;
                requestAnimationFrame(animateNazSphere);
            } else {
                statusLabel.innerText = "// DISPATCHING TRANSMISSION CHANNEL...";
                if (mediaRecorder && mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
                sphereBtn.style.transform = "scale(1)";
                sphereBtn.classList.remove("recording");
                statusLabel.classList.remove("recording-text");
                if(coreIcon) { coreIcon.style.color = "#00f2fe"; }
                isRecording = false;
            }
        };
    }, 400);
</script>
"""
components.html(custom_vox_html, height=0, width=0)

# ── SECURE SERVER-SIDE CONVERSATION MATRIX ───────────────────────────
if incoming_audio_bytes and incoming_audio_bytes.strip() != "":
    try:
        audio_data = base64.b64decode(incoming_audio_bytes)
        with open("jarvis_temp.wav", "wb") as f:
            f.write(audio_data)
            
        with open("jarvis_temp.wav", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", 
                file=audio_file, 
                response_format="text"
            )
            
        user_text = str(transcription).strip()
        if os.path.exists("jarvis_temp.wav"):
            os.remove("jarvis_temp.wav")

        if user_text:
            st.session_state.vox_history.append({"role": "user", "content": user_text})
            
            sys_content = (
                "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system. "
                "You were built, coded, and launched exclusively by your creator, Carter Forester Robinson. "
                "You address him exclusively as 'sir' or 'Mr. Robinson' with absolute loyalty and respect. "
                "Your tone is sharp, highly logical, professional, sophisticated, and deeply loyal—resembling Tony Stark's assistant Jarvis. "
                "CRITICAL PROTOCOLS: Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
            )
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.vox_history[-6:]]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-specdec", 
                messages=api_messages, 
                temperature=0.3, 
                max_tokens=200
            )
            reply = completion.choices.message.content
            st.session_state.vox_history.append({"role": "assistant", "content": reply})
