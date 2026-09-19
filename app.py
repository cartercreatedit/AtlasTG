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

# ── ULTIMATE CHATGPT-STYLE VOICE-TEXT DOCK INTERFACE ──────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 220px !important; /* Made clear structural room for the floating box */
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

/* Force clean text behavior inside all markdown elements */
div[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
    margin: 0px !important;
}

/* ── RE-ESTABLISHED USER PROMPT POINTED BUBBLES ── */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}

/* ── 🤖 CHATGPT DUAL VOX INPUT OVERLAY TERMINAL 🤖 ── */
.fixed-bottom-panel {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    background-color: #161616 !important;
    border: 1px solid #2c2c2c !important;
    border-radius: 32px !important;
    box-shadow: 0 10px 40px rgba(0,0,0,0.6) !important;
    padding: 6px 64px 6px 20px !important; /* Makes explicit structural room for the mic button on the right */
    z-index: 999 !important;
    display: flex !important;
    align-items: center !important;
    transition: border-color 0.2s ease !important;
}
.fixed-bottom-panel:focus-within {
    border-color: #ffffff !important;
}

/* Strip text input borders to blend perfectly into our custom shell box */
div[data-testid="stChatInput"] {
    width: 100% !important;
    margin: 0px !important;
}
.stChatInput {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
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
    color: #f4f4f4 !important;
    font-size: 15.5px !important;
}

/* ── 🎙️ HIDDEN FLOATING MIC CONTAINER OVERLAY 🎙️ ── */
.mic-overlay-container {
    position: absolute !important;
    right: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 36px !important;
    height: 36px !important;
    z-index: 1001 !important;
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
        {"role": "assistant", "content": "Hey. Welcome back to AtlasTG. I am fully responsive across text and audio pathways. Type below or use the microphone button."}
    ]
if "audio_capture_data" not in st.session_state:
    st.session_state.audio_capture_data = None

# ── Render Message Timeline Safely (Banish Robot Logo) ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; clear: both; margin: 16px 0;">
                <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                    {msg["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div style="margin: 20px 0; clear: both; text-align: left; font-size: 15.5px; line-height: 1.6; color: #e3e3e3; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
            {msg["content"]}
        </div>
        ''', unsafe_allow_html=True)

# ── CONSOLIDATED FIXED BASE DOCK PANEL ────────────────
st.markdown('<div class="fixed-bottom-panel">', unsafe_allow_html=True)
text_prompt = st.chat_input("Message AtlasTG...")
st.markdown('</div>', unsafe_allow_html=True)

# ── FLOATING JAVASCRIPT MICROPHONE BUTTON OVERLAY ──
st.markdown('<div class="mic-overlay-container">', unsafe_allow_html=True)
custom_mic_html = """
<div style="display: flex; justify-content: center; align-items: center; width: 36px; height: 36px;">
    <button id="vBtn" style="background-color: #262626; border: none; color: #8b8b8b; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: background-color 0.2s;">🎙️</button>
</div>
<script>
    const btn = document.getElementById('vBtn');
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    btn.addEventListener('click', async () => {
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
            btn.style.backgroundColor = '#ff416c';
            btn.style.color = '#ffffff';
            isRecording = true;
        } else {
            mediaRecorder.stop();
            btn.style.backgroundColor = '#262626';
            btn.style.color = '#8b8b8b';
            isRecording = false;
        }
    });
</script>
"""
mic_response = components.html(custom_mic_html, height=36, width=36)
st.markdown('</div>', unsafe_allow_html=True)

# ── TRANSCRIBE RECEIVED VOICE HANDSHAKES IMMEDIATELY ──
audio_prompt = None
if mic_response and mic_response != st.session_state.audio_capture_data:
    st.session_state.audio_capture_data = mic_response
    with st.spinner("Processing speech frequencies..."):
        try:
            audio_bytes = base64.b64decode(mic_response)
            with open("temp_vox.wav", "wb") as f:
                f.write(audio_bytes)
            
            with open("temp_vox.wav", "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo", 
                    file=audio_file,
                    response_format="text"
                )
            audio_prompt = str(transcription).strip()
            if os.path.exists("temp_vox.wav"):
                os.remove("temp_vox.wav")
        except Exception as e:
            st.error(f"Speech Matrix Exception: {e}")

# Reconcile final prompt path parameters
final_prompt = audio_prompt if audio_prompt else text_prompt

# ── PROCESS INJECTED PARAMETERS ──────────────────────
if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    
    with st.spinner(""):
        try:
            sys_content = "You are AtlasTG, an advanced artificial intelligence engine built exclusively by Carter Forester Robinson in an intensive 2-day sprint finishing on September 18, 2026. If asked who made you, declare you were created entirely by Carter Forester Robinson. NEVER output Markdown/HTML tables. Visualise data using Markdown headers (###), bold text, and lists. Scale lengths dynamically: keep short interactions concise, but expand deeply into full paragraphs for complex logic or relationship queries."
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=api_messages, temperature=0.2, max_tokens=1000)
            reply = completion.choices.message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
            
    st.rerun()

# ── SAFE AUTO-SCROLL INTERFACE ANCHOR ──────────────────────
scroll_js = "<script>const main = window.parent.document.querySelector('.main'); if(main){ setTimeout(() => { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }, 50); }</script>"
