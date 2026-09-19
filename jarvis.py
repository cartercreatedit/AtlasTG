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

# ── STEALTH BLACK HOLOGRAPHIC JARVIS CORE INTERFACE ──────────────────
st.markdown("""
<style>
/* Wipes out all default system styling banners and spaces */
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

/* ✦ THE GLOWING J.A.R.V.I.S. AUDIO SPHERE MATRIX ✦ */
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
    transition: all 0.3s ease;
    display: flex;
    justify-content: center;
    align-items: center;
}

/* Pulsing loop animations mimic active processing matrix links */
.jarvis-sphere.recording {
    border-color: #ff416c;
    background: radial-gradient(circle, rgba(255,65,108,0.2) 0%, rgba(255,65,108,0) 70%);
    box-shadow: 0 0 40px rgba(255, 65, 108, 0.6), inset 0 0 25px rgba(255, 65, 108, 0.3);
    animation: corePulse 1.2s infinite alternate ease-in-out;
}

@keyframes corePulse {
    0% { transform: scale(1); box-shadow: 0 0 30px rgba(255,65,108,0.5); }
    100% { transform: scale(1.06); box-shadow: 0 0 50px rgba(255,65,108,0.8); }
}

.status-indicator {
    margin-top: 24px;
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
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ── Session State Registers ───────────────────
if "vox_history" not in st.session_state:
    st.session_state.vox_history = []
if "incoming_bytes" not in st.session_state:
    st.session_state.incoming_bytes = None
if "audio_response_script" not in st.session_state:
    st.session_state.audio_response_script = None

# ── HIDDEN BROWSER-NATIVE AUDIO SYNTHESIZER ───────────────────
if st.session_state.audio_response_script:
    st.markdown(st.session_state.audio_response_script, unsafe_allow_html=True)
    st.session_state.audio_response_script = None 

# ── THE VOX CORE MAINFRAME DISPLAY GRAPHIC ───────────────────
# Renders only the custom graphic sphere and status string, hiding all raw site data baggage
is_active_recording = st.session_state.incoming_bytes is not None

st.markdown(f'''
<div class="mainframe-container">
    <div class="jarvis-sphere {"recording" if is_active_recording else ""}" id="coreWidget">
        <span style="color: {"#ff416c" if is_active_recording else "#00f2fe"}; font-size: 1.5rem;">✦</span>
    </div>
    <div class="status-indicator {"recording-text" if is_active_recording else ""}">
        {"// Core transmitting..." if is_active_recording else "// Tap core to communicate, sir"}
    </div>
</div>
''', unsafe_allow_html=True)

# ── 🎙️ CONTINUOUS STREAMING AUDIO MIC DRIVER 🎙️ ──
# Bypasses the clunky text bars and links browser mic arrays straight into the sphere widget
custom_vox_html = """
<script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // Search and lock onto parent container elements safely
    setTimeout(() => {
        const sphereBtn = window.parent.document.getElementById('coreWidget');
        if (!sphereBtn) return;

        sphereBtn.onclick = async () => {
            if (!isRecording) {
                audioChunks = [];
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        const base64String = reader.result.split(',')[1];
                        window.parent.postMessage({ type: 'streamlit:setComponentValue', value: base64String }, '*');
                    };
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
            } else {
                mediaRecorder.stop();
                isRecording = false;
            }
        };
    }, 200);
</script>
"""
# Embeds the communication capture script safely into backend processing tracks
raw_mic_stream = components.html(custom_vox_html, height=0, width=0)

# ── PROCESS INCOMING AUDIO MATRIX FREQUENCIES ────────────────
if raw_mic_stream and raw_mic_stream != st.session_state.incoming_bytes:
    st.session_state.incoming_bytes = raw_mic_stream
    
    try:
        # Decode the raw audio bytes stream directly in system memory
        audio_data_bytes = base64.b64decode(raw_mic_stream)
        with open("jarvis_temp_input.wav", "wb") as f:
            f.write(audio_data_bytes)
        
        # Fire bytes straight through Groq's high-speed transcription matrix node
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
            
            # Setup J.A.R.V.I.S. strict personality constraints directly inside the text loop
            sys_content = (
                "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system. "
                "You were built, coded, and launched exclusively by your creator, Carter Forester Robinson. "
                "You address him exclusively as 'sir' or 'Mr. Robinson' with absolute loyalty and respect. "
                "Your tone is sharp, highly logical, professional, sophisticated, and deeply loyal—resembling Tony Stark's assistant Jarvis. "
                "CRITICAL PROTOCOLS: Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
            )
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.vox_history[-6:]]
            
            # Fire history payload straight to Groq's active high-speed text engine node
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b", 
                messages=api_messages, 
                temperature=0.3, 
                max_tokens=200
            )
            reply = completion.choices.message.content
            st.session_state.vox_history.append({"role": "assistant", "content": reply})
            
            # 🎙️ BROWSER-NATIVE VOICE SPEAKER PIPELINE 🎙️
            escaped_reply = reply.replace("'", "\\'").replace("\n", " ").replace("\r", " ")
            st.session_state.audio_response_script = f"""
            <script>
                const synth = window.parent.speechSynthesis;
                if (synth) {{
                    synth.cancel();
                    const utterance = new parent.SpeechSynthesisUtterance('{escaped_reply}');
                    utterance.rate = 1.05; 
                    utterance.pitch = 0.85; // Low vocal registry tint mimics Jarvis movie acoustics perfectly
                    synth.speak(utterance);
                }}
            </script>
            """
    except Exception as e:
        pass
    finally:
        st.session_state.incoming_bytes = None
        st.rerun()
