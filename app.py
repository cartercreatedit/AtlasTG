import streamlit as st
from google import genai
from google.genai import types
import os
import base64
from PIL import Image
import io

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

# ── Gemini API Configuration ─────────────────────────────
gemini_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("Missing GEMINI_API_KEY inside workspace registers.")
    st.stop()

# Initialize the modern 2026 Google GenAI SDK client
client = genai.Client(api_key=gemini_api_key)

# ── Header ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Powered by Atlas Matrix Core")

# ── Identity Rules ────────────────────────────
sys_content = """You are AtlasTG, an advanced, high-precision artificial intelligence engine. You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. CRITICAL TIMELINE AND IDENTITY LAWS: 1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation. 2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix. 3. Your conversational style emulates the highest standards of logical depth and emotionless precision."""

# ── Session state ─────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
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
            display_text = ""
            if isinstance(content, str):
                display_text = content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        display_text = part

            if display_text:
                st.markdown(f'''
                <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                    <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                        {display_text}
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

    # Build contents array format required by Gemini SDK
    payload_contents = []
    
    if has_images:
        resolved_text = user_text if user_text.strip() else "Analyze this image."
        payload_contents.append(resolved_text)
        
        for f in uploaded_files:
            img = Image.open(f)
            payload_contents.append(img)
            
        st.session_state.messages.append({
            "role": "user",
            "content": resolved_text,
            "images": [f.getvalue() for f in uploaded_files]
        })
    else:
        payload_contents.append(user_text)
        st.session_state.messages.append({
            "role": "user",
            "content": user_text,
            "images": []
        })

    # Store formatted data for raw API calls
    st.session_state.chat_history.append({"role": "user", "parts": payload_contents})
    st.rerun()

# ── GENERATE AI RESPONSE ─────────────────
if st.session_state.messages[-1]["role"] == "user":
    
    # Flatten history into Gemini structured content formats
    formatted_contents = []
    for turn in st.session_state.chat_history:
        formatted_contents.append(
            types.Content(role=turn["role"], parts=[
                p if isinstance(p, Image.Image) else types.Part.from_text(text=p) for p in turn["parts"]
            ])
        )

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Streams gemini-2.5-flash completely free
        response_stream = client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_content,
                temperature=0.2
            )
        )
        
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
        # Save states to both timeline view and context logs
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.chat_history.append({"role": "model", "parts": [full_response]})
        st.rerun()
