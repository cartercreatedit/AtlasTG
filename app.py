import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
import io
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── RESTORED ORIGINAL BORDERLESS STEALTH STYLING ─────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 220px !important; /* Explicit vertical space for the custom bottom panel layout */
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
    border-top-right-radius: 2px !important; /* Pointed sharp tail top right secured back */
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

/* ── PREMIUM BORDERLESS FIXED DUAL PANEL (HIDES ACCIDENT OVERLAYS) ── */
.fixed-bottom-panel {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    background-color: #161616 !important;
    border: none !important;
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 16px !important;
    z-index: 999 !important;
    display: flex !important;
    align-items: center !important;
}

/* Strip inner input constraints entirely to float flat inside parent shell */
div[data-testid="stChatInput"] {
    width: 100% !important;
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

/* Circular elegant plus button anchor */
div.stButton > button {
    background-color: #262626 !important;
    border: none !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
    color: #8b8b8b !important;
    font-size: 1.25rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background-color 0.2s, color 0.2s !important;
}
div.stButton > button:hover {
    background-color: #363636 !important;
    color: #ffffff !important;
}

/* Floating custom file module drawer overlay */
div[data-testid="stFileUploader"] {
    background-color: #111111 !important;
    border: 1px dashed #2c2c2c !important;
    border-radius: 16px !important;
    padding: 10px !important;
    margin-bottom: 12px !important;
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

# ── Helper ────────────────────────────────────
def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Welcome back to AtlasTG. I am fully restored. Send a text or use the plus icon to feed me image data arrays."}
    ]
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# ── Render Message Timeline using Native Safe Structures ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            content = msg["content"]
            if isinstance(content, list):
                # Unpack compound multimodal user text elements safely
                for part in content:
                    if part["type"] == "text":
                        st.markdown(f'''
                        <div style="display: flex; justify-content: flex-end; width: 100%; clear: both; margin: 12px 0;">
                            <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                                {part["text"]}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            elif isinstance(content, str) and content:
                st.markdown(f'''
                <div style="display: flex; justify-content: flex-end; width: 100%; clear: both; margin: 12px 0;">
                    <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                        {content}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            if "images" in msg and msg["images"]:
                for img in msg["images"]:
                    st.image(img, width=280)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── INTEGRATED CHATGPT INTEGRATED LAYOUT DOCK PANEL ────
# Locks the file box directly on top of the text frame so it never messes up your alignment tracking
if st.session_state.show_uploader:
    uploaded_file = st.file_uploader("Select image payload data", type=["png", "jpg", "jpeg", "webp"], key="file_uploader", label_visibility="collapsed")
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file
        st.session_state.show_uploader = False
        st.rerun()

st.markdown('<div class="fixed-bottom-panel">', unsafe_allow_html=True)
col_plus, col_input = st.columns([0.07, 0.93], gap="small")
with col_plus:
    if st.button("＋", key="plus_btn"):
        st.session_state.show_uploader = not st.session_state.show_uploader
        st.rerun()
with col_input:
    prompt = st.chat_input("Message AtlasTG...")
st.markdown('</div>', unsafe_allow_html=True)

# ── PROCESS INPUT PARAMETERS ───────────────────────
if prompt:
    uploaded_file = st.session_state.uploaded_image
    has_images = uploaded_file is not None

    if has_images:
        image = Image.open(uploaded_file)
        b64_image = image_to_base64(image)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
        ]
        st.session_state.messages.append({
            "role": "user",
            "content": user_content,
            "images": [uploaded_file]
        })
        st.session_state.uploaded_image = None
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner(""):
        try:
            sys_content = (
                "You are AtlasTG, an advanced, high-precision artificial intelligence engine. "
                "You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. "
                "CRITICAL TIMELINE AND IDENTITY LAWS: "
