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

# ── Multi-Vendor Secure API Keys ─────────────────────────────────────
groq_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") or ""
eleven_key = st.secrets.get("ELEVEN_API_KEY") or os.getenv("ELEVEN_API_KEY") or ""
voice_id = st.secrets.get("ELEVEN_VOICE_ID") or "bfGb7JTLUnZebZRiFYyq"

if not groq_key:
    st.error("Missing GROQ_API_KEY inside Secrets registers.")
    st.stop()
if not eleven_key or not voice_id:
    st.error("Missing ElevenLabs credentials inside Secrets registers.")
    st.stop()

client = Groq(api_key=groq_key)

# ── Session State Registers ──────────────────────────────────────────
if "vox_history" not in st.session_state:
    st.session_state.vox_history = [
        {"role": "system", "content": "You are J.A.R.V.I.S., an advanced AI assistant built exclusively by Carter Forester Robinson. You address him as sir or Mr. Robinson with deep loyalty. Your tone is sharp, logical, professional, and sophisticated. Keep responses short and conversational (1-3 sentences max). Never use markdown, bold tags, or lists."}
    ]
if "audio_out" not in st.session_state:
    st.session_state.audio_out = None

# Inject hidden audio player when voice bytes stream back
if st.session_state.audio_out:
    st.markdown(st.session_state.audio_out, unsafe_allow_html=True)
    st.session_state.audio_out = None

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
</style>
""", unsafe_allow_html=True)

# ── FRONT-END INTERACTION ENGINE ─────────────────────────────────────
jarvis_frontend_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body, html {
        background-color: #000000;
        margin: 0; padding: 0;
        width: 100vw; height: 100vh;
        overflow: hidden;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .jarvis-sphere {
        width: 140px; height: 140px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,242,254,0.15) 0%, rgba(0,242,254,0) 70%);
        border: 2px solid #00f2fe;
        box-shadow: 0 0 30px rgba(0,242,254,0.4), inset 0 0 20px rgba(0,242,254,0.2);
        cursor: pointer;
        transition: transform 0.05s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        display: flex; justify-content: center; align-items: center;
    }
    .jarvis-sphere.recording {
        border-color: #ff416c;
        background: radial-gradient(circle, rgba(255,65,108,0.2) 0%, rgba(255,65,108,0) 70%);
        box-shadow: 0 0 40px rgba(255,65,108,0.6), inset 0 0 25px rgba(255,65,108,0.3);
    }
    .status-indicator {
        margin-top: 32px; color: #00f2fe;
        font-size: 0.8rem; letter-spacing: 2px;
        text-transform: uppercase; opacity: 0.6;
    }
    .recording-text { color: #ff416c !important; opacity: 1 !important; }
</style>
</head>
<body>
<div style="display:flex; flex-direction:column; justify-content:center; align-items:center; width:100vw; height:100vh;">
    <div class="jarvis-sphere" id="coreWidget"><span id="coreIcon" style="color:#00f2fe; font-size:1.5rem; transition:color 0.3s;">✦</span></div>
    <div class="status-indicator" id="statusLabel">// TAP ONCE TO AWAKEN SYSTEM PROTOCOLS</div>
</div>

<script>
    let mediaRecorder; let audioChunks = []; let isRecording = false;
    let audioContext; let analyser; let dataArray; let bufferLength; let streamRef;
    let silenceStart = null; const SILENCE_THRESHOLD = 8; const SILENCE_DURATION = 1500;

    const sphereBtn = document.getElementById('coreWidget');
    const statusLabel = document.getElementById('statusLabel');
    const coreIcon = document.getElementById('coreIcon');

    sphereBtn.onclick = async () => {
        if (!isRecording) {
            audioChunks = [];
            statusLabel.innerText = "// INITIALIZING SYSTEM CONSOLE...";
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                streamRef = stream;
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
                
                mediaRecorder.onstop = () => {
                    statusLabel.innerText = "// CONVERTING FREQUENCY MATRIX...";
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
                bufferLength = analyser.frequencyBinCount;
                dataArray = new Uint8Array(bufferLength);

                statusLabel.innerText = "// LISTENING CORE ONLINE...";
                statusLabel.classList.add("recording-text");
                sphereBtn.classList.add("recording");
                coreIcon.style.color = "#ff416c";
                isRecording = true;
                silenceStart = Date.now();
                mediaRecorder.start();
                requestAnimationFrame(monitorAudioStreamLoop);
            } catch (err) {
                statusLabel.innerText = "// HARDWARE ERROR: MIC ACCESS REJECTED";
            }
        } else {
            isRecording = false;
            if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
        }
    };

    function monitorAudioStreamLoop() {
        if (!isRecording) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0; for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
        let average = sum / bufferLength;
        let scaleValue = 1 + (average / 120); if (scaleValue > 1.45) scaleValue = 1.45;
        sphereBtn.style.transform = "scale(" + scaleValue + ")";

        if (average < SILENCE_THRESHOLD) {
            if (silenceStart === null) silenceStart = Date.now();
            else if (Date.now() - silenceStart > SILENCE_DURATION) {
                isRecording = false;
                if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
                return;
            }
        } else { silenceStart = null; }
        requestAnimationFrame(monitorAudioStreamLoop);
    }
</script>
</body>
</html>
"""

incoming_audio_payload = components.html(jarvis_frontend_html, height=700, scrolling=False)

# ── BACK-END PROCESSING CORE (FLATTENED LAYOUT - NO NESTED TRY LOGIC) ──
if incoming_audio_payload and isinstance(incoming_audio_payload, str) and incoming_audio_payload.strip() != "":
    audio_data = base64.b64decode(incoming_audio_payload)
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
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec", 
            messages=st.session_state.vox_history[-6:], 
            temperature=0.3, 
            max_tokens=200
        )
        reply = completion.choices.message.content
        st.session_state.vox_history.append({"role": "assistant", "content": reply})
        
        if eleven_key and voice_id:
            escaped_reply = reply.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
            
            raw_js = '<script>(async()=>{try{const res=await fetch("https://elevenlabs.io",{method:"POST",headers:{"xi-api-key":"ELEVEN_KEY","Content-Type":"application/json"},body:JSON.stringify({text:"REPLY_TEXT",model_id:"eleven_monolingual_v1",voice_settings:{stability:0.75,similarity_boost:0.85}})});if(res.status===200){const buf=await res.arrayBuffer();const url=URL.createObjectURL(new Blob([buf],{type:"audio/mp3"}));const audio=new Audio(url);audio.play();}}catch(e){}})();</script>'
            raw_js = raw_js.replace("VOICE_ID", voice_id)
            raw_js = raw_js.replace("ELEVEN_KEY", eleven_key)
            raw_js = raw_js.replace("REPLY_TEXT", escaped_reply)
            st.session_state.audio_out = raw_js

    st.rerun()
