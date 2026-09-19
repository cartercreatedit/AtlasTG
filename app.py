import streamlit as st
from groq import Groq
import os
import base64
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── PREMIUM MINIMAL STEALTH STYLING ─────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 160px !important;
    max-width: 760px;
    min-height: 100vh;
}
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden;
}
h1 {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 1.75rem !important;
}
.stCaption {
    color: #8b8b8b !important;
}

/* Clear default Streamlit padding baggage */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}

/* Force clean text behavior inside all markdown elements */
div[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
}

/* ── RE-ESTABLISHED USER PROMPT POINTED BUBBLES ── */
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) {
    display: flex !important;
    justify-content: flex-end !important;
    margin: 16px 0 !important;
}
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) > div:nth-child(2) {
    background-color: #1a1a1a !important;
    border: 1px solid #2d2d2d !important;
    padding: 12px 18px !important;
    border-radius: 18px !important;
    border-top-right-radius: 2px !important;
    max-width: 80% !important;
    display: inline-block !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
}

/* Assistant Plain Text Layout */
div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) {
    display: flex !important;
    justify-content: flex-start !important;
    margin: 16px 0 !important;
}
div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) > div:nth-child(2) {
    background-color: transparent !important;
    border: none !important;
    padding: 4px 0px !important;
    box-shadow: none !important;
    max-width: 100% !important;
}

/* ── EXACT CHATGPT TEXT BOX MATCH WITH BRIGHT WHITE OUTLINE FOCUS ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #161616 !important;
    border: 1px solid #2c2c2c !important;
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 20px !important; 
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stChatInput:focus-within {
    border-color: #ffffff !important;
    box-shadow: 0 0 0 1px #ffffff, 0 4px 30px rgba(255,255,255,0.05) !important;
}

/* Obliterate inner background border constraints */
div[data-testid="stChatInput"] *,
.stChatInput div[data-baseweb="textarea"],
.stChatInput div[data-baseweb="base-input"],
.stChatInput textarea {
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
}
.stChatInput textarea {
    color: #f4f4f4 !important;
    font-size: 15.5px !important;
}

/* 🎙️ FUTURISTIC VOICE ACTIVATION OVERLAY PANEL 🎙️ */
.voice-panel-box {
    background-color: #0d0d11 !important;
    border: 1px solid #252530 !important;
    border-radius: 20px !important;
    padding: 20px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.7) !important;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ── API Key Configuration ─────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ── Header ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Audio-Text Intelligence Engine · Coded by C. F. Robinson")

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Welcome back to AtlasTG. Text intelligence is active below, or check the box to initialize the intelligent auto-stopping voice matrix."}
    ]
if "audio_base64" not in st.session_state:
    st.session_state.audio_base64 = None

# ── Header Dynamic Tab Switcher ──────────────────
voice_mode_active = st.checkbox("🎙️ Initialize Intelligent Auto-Stop Voice Core", value=False)

audio_prompt = None

# ── 🎙️ CUSTOM AUTO-STOPPING JAVASCRIPT MICROPHONE 🎙️ ──
if voice_mode_active and not st.session_state.audio_base64:
    st.markdown('<div class="voice-panel-box">', unsafe_allow_html=True)
    st.markdown('<p style="color:#00f2fe; font-size:0.85rem; letter-spacing:1px; margin-bottom:8px; font-weight:bold;">// AUTO-SENSING AUDIO CORE ACTIVE</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b8b8b; font-size:0.75rem;">Speak normally. The engine will auto-detect silence and close the transmission stream immediately.</p>', unsafe_allow_html=True)
    
    # Custom HTML5 Component capturing microphone thresholds and auto-submitting upon 1.5s of silence
    custom_mic_html = """
    <div style="display: flex; justify-content: center; align-items: center; padding: 10px;">
        <button id="micBtn" style="background-color: #ff416c; border: none; color: white; padding: 10px 24px; font-family: monospace; border-radius: 20px; font-weight: bold; cursor: pointer; box-shadow: 0 0 15px rgba(255, 65, 108, 0.4);">🎤 RECORDING...</button>
    </div>
    <script>
        let mediaRecorder;
        let audioChunks = [];
        let audioContext;
        let analyser;
        let streamFile;
        let silenceTimeout;

        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            streamFile = stream;
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    window.parent.postMessage({ type: 'streamlit:setComponentValue', value: base64data }, '*');
                };
            };

            // Set up audio monitoring algorithms to detect natural user speech pauses
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyse || audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            mediaRecorder.start();

            function checkSilence() {
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
                let average = sum / bufferLength;

                if (average < 8) { // Silence volume threshold anchor
                    if (!silenceTimeout) {
                        silenceTimeout = setTimeout(() => {
                            if (mediaRecorder.state === "recording") {
                                mediaRecorder.stop();
                                streamFile.getTracks().forEach(track => track.stop());
                                audioContext.close();
                            }
                        }, 1500); // Auto-stops exactly after 1.5 seconds of silence
                    }
                } else {
                    clearTimeout(silenceTimeout);
                    silenceTimeout = null;
                }
                if (mediaRecorder.state === "recording") {
                    requestAnimationFrame(checkSilence);
                }
            }
            requestAnimationFrame(checkSilence);
        }).catch(err => {
            console.error("Microphone Access Blocked: " + err);
        });
    </script>
    """
    # Renders the auto-sensing container safely into Streamlit layout views
    mic_value = components.html(custom_mic_html, height=100)
    
    # Process base64 strings returned natively by the browser macro handler
    if mic_value:
        st.session_state.audio_base64 = mic_value
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

# ── TRANSCRIBE RECEIVED BASE64 CHUNKS IMMEDIATELY ───────
if st.session_state.audio_base64:
    with st.spinner("Processing speech frequencies..."):
        try:
            raw_data = base64.b64decode(st.session_state.audio_base64)
            with open("temp_voice_input.wav", "wb") as f:
                f.write(raw_data)
            
            with open("temp_voice_input.wav", "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo", 
                    file=audio_file,
                    response_format="text"
                )
            audio_prompt = str(transcription).strip()
            
            if os.path.exists("temp_voice_input.wav"):
                os.remove("temp_voice_input.wav")
        except Exception as e:
            st.error(f"Speech Matrix Exception: {e}")
        finally:
