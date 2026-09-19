import streamlit as st
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

# Inject hidden audio player when voice bytes stream back from ElevenLabs
if st.session_state.audio_out:
    st.markdown(st.session_state.audio_out, unsafe_allow_html=True)
    st.session_state.audio_out = None

# ── STEALTH HOLOGRAPHIC CONSOLE STYLING ──────────────────────────────
st.markdown("""
<style>
.stApp, .main, .block-container {
    background-color: #000000 !important;
    padding-top: 2rem !important;
    max-width: 760px;
    min-height: 100vh;
}
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden !important;
}
/* Premium Borderless Midnight Text Box */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #0d0d12 !important;
    border: 1px solid #1a1a24 !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,242,254,0.1) !important;
    padding: 6px 12px 6px 20px !important; 
}
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
    color: #00f2fe !important;
    font-family: monospace !important;
    font-size: 15px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Mainframe Boot Header ────────────────────────────────────────────
st.markdown("<h2 style='color:#ffffff; font-weight:normal; font-family:monospace;'>✦ J.A.R.V.I.S. Mainframe</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#00f2fe; font-size:0.8rem; letter-spacing:1px; font-family:monospace;'>// SYSTEM STATUS: CORE ACTIVE · ARCHITECT: C. F. ROBINSON</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #1a1a24; margin-bottom: 2rem;'>", unsafe_allow_html=True)

# ── CONSOLE COMMAND INPUT ──────────────────────────────────────────
user_command = st.chat_input("Input mainframe command directive, sir...")

if user_command:
    st.session_state.vox_history.append({"role": "user", "content": user_command})
    
    # Process text logic instantly using active Llama nodes
    completion = client.chat.completions.create(
        model="llama-3.3-70b-specdec", 
        messages=st.session_state.vox_history[-6:], 
        temperature=0.3, 
        max_tokens=200
    )
    reply = completion.choices.message.content
    st.session_state.vox_history.append({"role": "assistant", "content": reply})
    
    # Stream text straight over to ElevenLabs to compile an exact voice clone tracking audio array
    if eleven_key and voice_id:
        escaped_reply = reply.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
        
        # Single-line script string formulation prevents inner variable break leaks
        raw_js = '<script>(async()=>{try{const res=await fetch("https://elevenlabs.io",{method:"POST",headers:{"xi-api-key":"ELEVEN_KEY","Content-Type":"application/json"},body:JSON.stringify({text:"REPLY_TEXT",model_id:"eleven_monolingual_v1",voice_settings:{stability:0.75,similarity_boost:0.85}})});if(res.status===200){const buf=await res.arrayBuffer();const url=URL.createObjectURL(new Blob([buf],{type:"audio/mp3"}));const audio=new Audio(url);audio.play();}}catch(e){}})();</script>'
        raw_js = raw_js.replace("VOICE_ID", voice_id)
        raw_js = raw_js.replace("ELEVEN_KEY", eleven_key)
        raw_js = raw_js.replace("REPLY_TEXT", escaped_reply)
        st.session_state.audio_out = raw_js
        
    st.rerun()
