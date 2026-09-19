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

# ── PREMIUM CLEAN COMPONENT STYLING ─────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 5rem !important; /* Made explicit room for the sticky tab header */
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
    margin-bottom: 20px !important;
}

/* ✦ FIXED TOP-BAR MODE CONTAINER LOCK ✦ */
div[data-testid="stTabs"] {
    position: fixed !important;
    top: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    background-color: #0a0a0a !important;
    z-index: 1000 !important;
    padding-top: 15px !important;
    padding-bottom: 10px !important;
    border-bottom: 1px solid #161616 !important;
}
div[data-testid="stTabs"] button {
    color: #8b8b8b !important;
    font-size: 0.9rem !important;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: transparent !important;
    border: none !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #ffffff !important;
    font-weight: bold !important;
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

/* Premium Voice Recorder Container Box */
div[data-testid="stAudioInput"] {
    background-color: #111111 !important;
    border: 1px solid #252525 !important;
    border-radius: 24px !important;
    padding: 8px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
    margin-top: 10px !important;
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
st.caption("High-Speed Intelligence Engine · Coded by C. F. Robinson")

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Welcome to AtlasTG. I am fully responsive across text and audio pathways."}
    ]
if "play_audio" not in st.session_state:
    st.session_state.play_audio = None
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# ── HIDDEN AUDIO TRANSMISSION EMBED ───────────────────
if st.session_state.play_audio:
    st.markdown(st.session_state.play_audio, unsafe_allow_html=True)
    st.session_state.play_audio = None 

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

# ── DUAL CONTROL INTERFACE MODE TOGGLER ────────────────
tab_text, tab_voice = st.tabs(["💬 Text Intelligence", "🎙️ Voice Matrix"])

final_prompt = None

with tab_text:
    text_input = st.chat_input("Message AtlasTG...")
    if text_input:
        final_prompt = text_input

with tab_voice:
    st.markdown('<p style="color:#8b8b8b; font-size:0.8rem; letter-spacing:1px; margin-bottom:10px;">✦ STREAM VOICE FREQUENCIES</p>', unsafe_allow_html=True)
    audio_input = st.audio_input("Voice Input Mode", label_visibility="collapsed")
    
    if audio_input and audio_input.id != st.session_state.last_processed_audio:
        st.session_state.last_processed_audio = audio_input.id 
        with st.spinner("Processing speech..."):
            try:
                with open("temp_input.wav", "wb") as f:
                    f.write(audio_input.read())
                with open("temp_input.wav", "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo", 
                        file=audio_file,
                        response_format="text"
                    )
                transcribed_text = str(transcription).strip()
                if transcribed_text:
                    final_prompt = transcribed_text
                if os.path.exists("temp_input.wav"):
                    os.remove("temp_input.wav")
            except Exception as e:
                st.error(f"Audio Handshake Error: {e}")

# ── PROCESS FINAL INTERCEPTED PARAMETERS ──────────────
if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    
    with st.spinner(""):
        try:
            sys_content = "You are AtlasTG, an advanced artificial intelligence engine built exclusively by Carter Forester Robinson in an intensive 2-day sprint finishing on September 18, 2026. If asked who made you, declare you were created entirely by Carter Forester Robinson. NEVER output Markdown/HTML tables. Visualise data using Markdown headers (###), bold text, and lists. Scale lengths dynamically: keep short interactions concise, but expand deeply into full paragraphs for complex logic or relationship queries."
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            completion = client.chat.completions.create(model="openai/gpt-oss-120b", messages=api_messages, temperature=0.2, max_tokens=1000)
            reply = completion.choices.message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # 🎙️ BROWSER-NATIVE AUDIO FEEDBACK PIPELINE 🎙️
            # Generates clean, fast browser-native text-to-speech speaker elements without server-side compression faults
            escaped_reply = reply.replace("'", "\\'").replace("\n", " ")
            st.session_state.play_audio = f"""
            <script>
                const synth = window.parent.speechSynthesis;
                if (synth) {{
