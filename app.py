import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
import io
import streamlit.components.v1 as components
import requests

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── ORIGINAL BORDERLESS GOOGLE-STYLE STYLING ─────────────────────────
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
/* ── USER PROMPT POINTED BUBBLES ── */
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
/* ── PREMIUM BORDERLESS MIDNIGHT TEXT BOX ── */
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
    border: none !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 20px !important; 
}
.stChatInput:focus-within {
    border: none !important;
    box-shadow: 0 4px 35px rgba(0,0,0,0.6) !important;
    outline: none !important;
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
</style>
""", unsafe_allow_html=True)

# ── Multi-Vendor API Configurations ─────────────────────
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not groq_api_key:
    st.error("Missing GROQ_API_KEY inside workspace registers.")
    st.stop()
if not openai_api_key:
    st.error("Missing OPENAI_API_KEY inside workspace registers.")
    st.stop()

groq_client = Groq(api_key=groq_api_key)

# ── Header ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Powered by Groq & OpenAI")

# ── Identity Rules ────────────────────────────
sys_content = """You are AtlasTG, an advanced, high-precision artificial intelligence engine. You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. CRITICAL TIMELINE AND IDENTITY LAWS: 1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation. 2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix. 3. Your conversational style emulates the highest standards of logical depth and emotionless precision."""

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Ask me any text prompt or logic question and I will solve it instantly. You can also attach images."}
    ]

# ── Render Message Timeline ───────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            content = msg["content"]
            if isinstance(content, str) and content:
                st.markdown(f'''
                <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                    <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                        {content}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            elif isinstance(content, list):
                for part in content:
                    if part["type"] == "text":
                        st.markdown(f'''
                        <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                            <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                                {part["text"]}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            
            if "images" in msg and msg["images"]:
                for img_bytes in msg["images"]:
                    st.image(img_bytes, width=280)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── CHAT INPUT WITH IMAGE UPLOAD (plus icon) ─────────────────────
prompt = st.chat_input(
    "Message AtlasTG...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"]
)

# ── PROCESS INPUT ──────────────────────
if prompt:
    user_text = prompt.text if prompt.text else ""
    uploaded_files = prompt.files if prompt.files else []
    has_images = len(uploaded_files) > 0

    if has_images:
        content_payload = [{"type": "text", "text": user_text}]
        for f in uploaded_files:
            bytes_data = f.getvalue()
            base64_image = base64.b64encode(bytes_data).decode("utf-8")
            content_payload.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{f.type};base64,{base64_image}"
                }
            })
            
        st.session_state.messages.append({
            "role": "user",
            "content": content_payload,
            "images": [f.getvalue() for f in uploaded_files]
        })
    else:
        st.session_state.messages.append({
            "role": "user",
            "content": user_text,
            "images": []
        })

    st.rerun()

# ── GENERATE AI RESPONSE ─────────────────
if st.session_state.messages[-1]["role"] == "user":
    api_messages = [{"role": "system", "content": sys_content}]
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            api_messages.append({
                "role": "user",
                "content": msg["content"]
            })
        elif msg["role"] == "assistant":
            api_messages.append({
                "role": "assistant",
                "content": msg["content"]
            })

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=api_messages,
                temperature=0.2,
                max_tokens=1024,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices and chunk.choices.delta and chunk.choices.delta.content:
                    full_response += chunk.choices.delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
