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

# ── ADVANCED CORE AUDIO-VISUAL STYLING ─────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 220px !important;
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

/* ── INTEGRATED MULTI-INPUT FIXED BASE PANEL ── */
.fixed-bottom-panel {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    background-color: #0a0a0a !important;
    padding-bottom: 24px !important;
    padding-top: 10px !important;
    z-index: 999 !important;
}

/* Exact borderless prompt frame match */
div[data-testid="stChatInput"] {
    width: 100% !important;
}
.stChatInput {
    background-color: #161616 !important;
    border: none !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 20px !important; 
}

/* OBLITERATE EVERY SINGLE HIDDEN INTERNAL BORDER AND BACKGROUND SHADOW */
div[data-testid="stChatInput"] *,
.stChatInput div[data-baseweb="textarea"],
.stChatInput div[data-baseweb="base-input"],
.stChatInput textarea {
    border: none !important;
    border-color: transparent !important;
    background-color: transparent !important;
    background: transparent !important;
    box-shadow: none !important;
    outline: none !important;
}
.stChatInput textarea {
    color: #f4f4f4 !important;
    font-size: 15.5px !important;
}

/* Custom styled container for native microphone framework layout */
div[data-testid="stAudioInput"] {
    margin-bottom: 12px !important;
    background-color: #111111 !important;
    border: 1px solid #222222 !important;
    border-radius: 20px !important;
    padding: 6px !important;
}

/* Speaker Trigger Link Style */
.stButton > button {
    background-color: transparent !important;
    border: 1px solid #2d2d2d !important;
    color: #8b8b8b !important;
    padding: 4px 12px !important;
    font-size: 0.8rem !important;
    border-radius: 20px !important;
    transition: color 0.2s ease, border-color 0.2s ease !important;
    margin-top: 4px !important;
}
.stButton > button:hover {
    color: #ffffff !important;
    border-color: #ffffff !important;
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
        {"role": "assistant", "content": "Hey. You can type a text prompt to me or record your voice right below—I will listen, reply on screen, and let you choose if you want to hear it out loud."}
    ]
if "play_audio" not in st.session_state:
    st.session_state.play_audio = None

# ── HIDDEN AUDIO TRANSMISSION EMBED ───────────────────
if st.session_state.play_audio:
    st.markdown(st.session_state.play_audio, unsafe_allow_html=True)
    st.session_state.play_audio = None 

# ── Render Message Timeline using Native Safe Structures ──────────────────
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; clear: both; margin: 12px 0;">
                <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                    {msg["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if idx > 0: 
            if st.button("Speak Answer 🔊", key=f"speak_{idx}"):
                with st.spinner(""):
                    try:
                        tts_response = client.audio.speech.create(
                            model="canopylabs/orpheus-v1-english",
                            voice="alloy", 
                            input=msg["content"]
                        )
                        audio_base64 = base64.b64encode(tts_response.content).decode('utf-8')
                        st.session_state.play_audio = f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="true" style="display:none;"></audio>'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Voice Synthesis Error: {e}")

# ── CONSOLIDATED FIXED BASE USER CAPTURE PANEL ────────
st.markdown('<div class="fixed-bottom-panel">', unsafe_allow_html=True)
audio_input = st.audio_input("Voice Input Mode", label_visibility="collapsed")
text_input = st.chat_input("Message AtlasTG...")
st.markdown('</div>', unsafe_allow_html=True)

# ── DOCK RECONCILIATION GATEWAYS ──────────────────────
final_prompt = None

if audio_input:
    with st.spinner(""):
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
elif text_input:
    final_prompt = text_input

# ── PROCESS FINAL INTERCEPTED PARAMETERS ──────────────
if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    
    with st.spinner(""):
        try:
            # IDENTITY SYSTEM DIRECTIVES DEFINED AS A FLAT CONCISE LITERAL STRING
            sys_content = "You are AtlasTG, an advanced artificial intelligence engine built exclusively by Carter Forester Robinson in an intensive 2-day sprint finishing on September 18, 2026. If asked who made you, declare you were created entirely by Carter Forester Robinson. NEVER output Markdown/HTML tables. Visualise data using Markdown headers (###), bold text, and lists. Scale lengths dynamically: keep short interactions concise, but expand deeply into full paragraphs for complex logic or relationship queries."
            
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            # FLAT SINGLE-LINE DESPATCH EXECUTION PREVENTS UNCLOSED BRACKET LOG FAULTS
            completion = client.chat.completions.create(model="openai/gpt-oss-120b", messages=api_messages, temperature=0.2, max_tokens=1000)
            
            reply = completion.choices.message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
            
    st.rerun()

# ── SAFE AUTO-SCROLL INTERFACE ANCHOR ──────────────────────
scroll_js = "<script>const main = window.parent.document.querySelector('.main'); if(main){ setTimeout(() => { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }, 50); }</script>"
components.html(scroll_js, height=0)
