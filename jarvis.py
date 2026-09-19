import streamlit as st
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

# ── Multi-Vendor Secure Server API Keys ──────────────────────────────
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
        {"role": "assistant", "content": "Mainframe channels active, sir. Standing by for command directive parameters."}
    ]
if "audio_out" not in st.session_state:
    st.session_state.audio_out = None

# Instantly trigger audio playback via native browser cache arrays
if st.session_state.audio_out:
    st.markdown(st.session_state.audio_out, unsafe_allow_html=True)
    st.session_state.audio_out = None

# ── ORIGINAL STYLING CONFIGURATIONS (ZERO TEXT-CLUTTER BAGGAGE) ──────
st.markdown("""
<style>
.stApp {
    background-color: #000000;
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

/* Clear default Streamlit padding baggage */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}

/* Force clean text behavior inside all markdown elements */
div[data-testid="stMarkdownContainer"] p {
    color: #00f2fe !important;
    font-family: monospace !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
}

/* User pointed layout bubbles re-established */
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) {
    display: flex !important;
    justify-content: flex-end !important;
    margin: 16px 0 !important;
}
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) > div:nth-child(2) {
    background-color: #111116 !important;
    border: 1px solid #1a1a24 !important;
    padding: 12px 18px !important;
    border-radius: 18px !important;
    border-top-right-radius: 2px !important;
    max-width: 80% !important;
    display: inline-block !important;
    box-shadow: 0 4px 15px rgba(0,242,254,0.1) !important;
}

/* Assistant hidden text plain layout rules */
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

/* Premium borderless input tray console dock */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #09090d !important;
    border: 1px solid #14141f !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,242,254,0.15) !important;
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
    color: #ffffff !important;
    font-size: 15.5px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Mainframe Header ─────────────────────────────────────────────────
st.markdown("<h1 style='font-family:monospace; font-weight:normal;'>✦ J.A.R.V.I.S. Core</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8b8b8b; font-size:0.8rem; letter-spacing:1px; font-family:monospace;'>SYSTEM BLUEPRINTS LIVE · ARCHITECT: CARTER FORESTER ROBINSON</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #14141f; margin-bottom: 2rem;'>", unsafe_allow_html=True)

# ── Render Message Timeline ──────────────────────────────────────────
for msg in st.session_state.vox_history:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# ── SINGLE INPUT CONSOLE COMMAND TRAYS ───────────────────────────────
user_command = st.chat_input("Input mainframe command directive, sir...")

if user_command:
    st.session_state.vox_history.append({"role": "user", "content": user_command})
    
    with st.spinner(""):
        sys_content = (
            "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system. "
            "You were built, coded, and launched exclusively by your creator, Carter Forester Robinson. "
            "You address him exclusively as 'sir' or 'Mr. Robinson' with absolute loyalty and respect. "
            "Your tone is sharp, highly logical, professional, sophisticated, and deeply loyal—resembling Tony Stark's assistant Jarvis. "
            "CRITICAL PROTOCOLS: Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
        )
        api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.vox_history[-6:]]
        
        # Fire text directly to Groq's secure server backend nodes safely
        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec", 
            messages=api_messages, 
            temperature=0.3, 
            max_tokens=200
        )
        reply = completion.choices.message.content
        st.session_state.vox_history.append({"role": "assistant", "content": reply})
        
        # Execute direct server-side endpoint pass to ElevenLabs (CORS blocks are impossible)
        try:
            tts_url = f"https://elevenlabs.io{voice_id}"
            headers = {
                "xi-api-key": eleven_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": reply,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.85
                }
            }
            response = requests.post(tts_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                b64_audio = base64.b64encode(response.content).decode("utf-8")
                st.session_state.audio_out = f"""
                <audio autoplay style="display:none;">
                    <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                </audio>
                """
        except Exception:
            pass
            
    st.rerun()
