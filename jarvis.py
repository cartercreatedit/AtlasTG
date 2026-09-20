import streamlit as st
from groq import Groq
import os
import base64
import streamlit.components.v1 as components

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── API Key Configuration ─────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY inside your Streamlit secrets panel.")
    st.stop()

client = Groq(api_key=api_key)

# ── Session State Registers ───────────────────
if "vox_history" not in st.session_state:
    st.session_state.vox_history = []
if "incoming_bytes" not in st.session_state:
    st.session_state.incoming_bytes = None
if "audio_response_script" not in st.session_state:
    st.session_state.audio_response_script = None

# Injects the browser voice synthesizer execution tags when response cycles trigger
if st.session_state.audio_response_script:
    st.markdown(st.session_state.audio_response_script, unsafe_allow_html=True)
    st.session_state.audio_response_script = None 

# ── THE VOX CORE MAINFRAME DISPLAY GRAPHIC ───────────────────
is_active_recording = st.session_state.incoming_bytes is not None

st.markdown(f'''
<style>
.stApp, .main, .block-container {{
    background-color: #000000 !important;
    padding: 0 !important; margin: 0 !important;
    width: 100vw !important; height: 100vh !important;
    overflow: hidden !important;
}}
#MainMenu, footer, header, .stDeployButton {{ visibility: hidden !important; }}

.mainframe-container {{
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    width: 100vw; height: 100vh; background-color: #000000;
    position: fixed; top: 0; left: 0; z-index: 999;
}}
.jarvis-sphere {{
    width: 140px; height: 140px; border-radius: 50%;
    background: radial-gradient(circle, rgba(0,242,254,0.15) 0%, rgba(0,242,254,0) 70%);
    border: 2px solid #00f2fe;
    box-shadow: 0 0 30px rgba(0, 242, 254, 0.4), inset 0 0 20px rgba(0, 242, 254, 0.2);
    cursor: pointer; display: flex; justify-content: center; align-items: center;
    transition: transform 0.05s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}}
.jarvis-sphere.recording {{
    border-color: #ff416c;
    background: radial-gradient(circle, rgba(255,65,108,0.2) 0%, rgba(255,65,108,0) 70%);
    box-shadow: 0 0 40px rgba(255, 65, 108, 0.6), inset 0 0 25px rgba(255, 65, 108, 0.3);
}}
.status-indicator {{
    margin-top: 32px; color: #00f2fe; font-family: monospace; font-size: 0.8rem;
    letter-spacing: 2px; text-transform: uppercase; opacity: 0.6;
    text-align: center;
}}
</style>

<div class="mainframe-container">
    <div class="jarvis-sphere {"recording" if is_active_recording else ""}" id="coreWidget">
        <span style="color: {"#ff416c" if is_active_recording else "#00f2fe"}; font-size: 1.5rem;" id="coreIcon">✦</span>
    </div>
    <div class="status-indicator" id="statusLabel">
        // TAP CORE TO COMMUNICATE, SIR
    </div>
</div>
''', unsafe_allow_html=True)

# ── THE RE-ENGINEERED BI-DIRECTIONAL EVENT BRIDGE TUNNEL ───────
custom_vox_html = """
<script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

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
                    statusLabel.innerText = "// SYNCHRONIZING CORE DATA ARRAYS...";
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        const base64String = reader.result.split(',');
                        window.parent.postMessage({ type: 'streamlit:setComponentValue', value: base64String }, '*');
                    };
                    stream.getTracks().forEach(track => track.stop());
                };

                statusLabel.innerText = "// LISTENING CORE ONLINE...";
                sphereBtn.classList.add("recording");
                if(coreIcon) { coreIcon.style.color = "#ff416c"; }
                mediaRecorder.start();
                isRecording = true;
            } else {
                statusLabel.innerText = "// DISPATCHING TRANSMISSION CHANNEL...";
                if (mediaRecorder && mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
                sphereBtn.classList.remove("recording");
                if(coreIcon) { coreIcon.style.color = "#00f2fe"; }
                isRecording = false;
            }
        };
    }, 400);
</script>
"""
raw_mic_stream = components.html(custom_vox_html, height=0, width=0)

# ── PROCESS INDEPENDENT DATA HANDSHAKES ──────────────────────────
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
            
            escaped_reply = reply.replace("'", "\\'").replace("\n", " ").replace("\r", " ")
            st.session_state.audio_response_script = f"""
            <script>
                const synth = window.parent.speechSynthesis;
                if (synth) {{
                    synth.cancel();
                    const utterance = new parent.SpeechSynthesisUtterance('{escaped_reply}');
                    utterance.rate = 1.05; 
                    utterance.pitch = 0.85; 
                    synth.speak(utterance);
                }}
                const label = window.parent.document.getElementById('statusLabel');
                if (label) {{ label.innerText = "// TAP CORE TO COMMUNICATE, SIR"; }}
            </script>
            """
    except Exception:
        pass
    finally:
        st.session_state.incoming_bytes = None
        st.rerun()
