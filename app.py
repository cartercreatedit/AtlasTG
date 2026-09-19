import streamlit as st
from groq import Groq
import os
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── ULTIMATE VOX CORE GRAPHICS CONFIGURATION ──────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 180px !important;
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
    padding: 24px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.7) !important;
    animation: slideDown 0.3s ease-out !important;
}
@keyframes slideDown {
    from { transform: translateY(-10px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Custom styled container for native microphone framework layout */
div[data-testid="stAudioInput"] {
    background-color: #16161e !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 28px !important;
    padding: 8px !important;
}

/* Minimalist Audio Trigger Link style */
.stButton > button[key="vox_toggle"] {
    background-color: transparent !important;
    border: 1px solid #2d2d2d !important;
    color: #8b8b8b !important;
    padding: 6px 16px !important;
    font-size: 0.85rem !important;
    border-radius: 20px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[key="vox_toggle"]:hover {
    color: #00f2fe !important;
    border-color: #00f2fe !important;
    box-shadow: 0 0 10px rgba(0, 242, 254, 0.15) !important;
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
        {"role": "assistant", "content": "Hey. Welcome back to AtlasTG. Text intelligence is active below, or click the link shortcut to slide open the voice core channel."}
    ]
if "voice_mode_active" not in st.session_state:
    st.session_state.voice_mode_active = False
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# ── 🎙️ MINIMALIST VOICE OVERLAY TRIGGER ────────────────
col_left, col_right = st.columns([0.7, 0.3])
with col_right:
    # Minimal toggle switch that protects your core layout design
    if st.button("🎙️ Voice Core Matrix", key="vox_toggle"):
        st.session_state.voice_mode_active = not st.session_state.voice_mode_active
        st.rerun()

# Dynamic slider drawer logic
audio_prompt = None
if st.session_state.voice_mode_active:
    st.markdown('<div class="voice-panel-box">', unsafe_allow_html=True)
    st.markdown('<p style="color:#00f2fe; font-size:0.85rem; letter-spacing:1px; margin-bottom:12px; font-weight:bold;">// AUDIO CAPTURE ARRAY STREAMING</p>', unsafe_allow_html=True)
    
    audio_capture = st.audio_input("Voice Input Mode", label_visibility="collapsed")
    
    if audio_capture and audio_capture.id != st.session_state.last_processed_audio:
        st.session_state.last_processed_audio = audio_capture.id
        with st.spinner("Processing speech frequencies..."):
            try:
                with open("temp_input.wav", "wb") as f:
                    f.write(audio_capture.read())
                with open("temp_input.wav", "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo", 
                        file=audio_file,
                        response_format="text"
                    )
                transcribed_text = str(transcription).strip()
                if transcribed_text:
                    audio_prompt = transcribed_text
                if os.path.exists("temp_input.wav"):
                    os.remove("temp_input.wav")
                
                # Auto-close panel on complete capture execution
                st.session_state.voice_mode_active = False
            except Exception as e:
                st.error(f"Audio Handshake Error: {e}")
                
    st.markdown('</div>', unsafe_allow_html=True)

# ── Render Message Timeline using Native Safe Structures ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                    {msg["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── SINGLE TEXT INPUT CONSOLE DOCK ─────────────────────
text_prompt = st.chat_input("Message AtlasTG...")

# Reconcile final prompt path parameters
final_prompt = audio_prompt if audio_prompt else text_prompt

# ── PROCESS INJECTED PARAMETERS ──────────────────────
if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    
    with st.spinner(""):
        try:
            sys_content = "You are AtlasTG, an advanced artificial intelligence engine built exclusively by Carter Forester Robinson in an intensive 2-day sprint finishing on September 18, 2026. If asked who made you, declare you were created entirely by Carter Forester Robinson. NEVER output Markdown/HTML tables. Visualise data using Markdown headers (###), bold text, and lists. Scale lengths dynamically: keep short interactions concise, but expand deeply into full paragraphs for complex logic or relationship queries."
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            # Locked onto un-throttled free production text node
