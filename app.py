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

# ── CSS Configuration ─────────────────────────
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

/* Hide default avatars completely */
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {
    display: none !important;
}

/* Clean message rows background clearing */
.stChatMessage {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
    margin: 16px 0px !important;
    width: 100% !important;
}

/* 👤 USER PROMPTS: Aligned Right inside an Exact Rectangular Bubble Shape */
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) {
    display: flex !important;
    justify-content: flex-end !important;
}
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) > div:nth-child(2) {
    background-color: #1a1a1a !important;
    border: 1px solid #2d2d2d !important;
    padding: 12px 18px !important;
    border-radius: 18px !important;
    border-top-right-radius: 2px !important; /* Pointed sharp tail top right */
    max-width: 80% !important;
    display: inline-block !important;
}

/* 🐆 ASSISTANT RESPONSES: Aligned Left as Clean Plain Text with NO Bubble Shapes */
div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) {
    display: flex !important;
    justify-content: flex-start !important;
}
div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) > div:nth-child(2) {
    background-color: transparent !important;
    border: none !important;
    padding: 0px !important;
    box-shadow: none !important;
    max-width: 100% !important;
}

/* Text alignment typography configuration */
div[data-testid="stMarkdownContainer"] p {
    color: #e3e3e3 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
    margin: 0px !important;
}

/* ── EXACT GOOGLE AI INPUT BOX MATCH WITH INTEGRATED INTERNAL PADDING ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}

/* Outer frame matches Gemini sizing with explicit left indentation */
.stChatInput {
    background-color: #161616 !important;
    border: 1px solid #2c2c2c !important;
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 48px !important; 
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

/* Sleek white active glow */
.stChatInput:focus-within {
    border-color: #ffffff !important;
    box-shadow: 0 0 0 1px #ffffff, 0 4px 30px rgba(255,255,255,0.05) !important;
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

/* Sizing text inside the container perfectly */
.stChatInput textarea {
    color: #f4f4f4 !important;
    font-size: 15.5px !important;
    padding: 8px 4px !important;
}

/* ── INJECTED PLUS ICON INSIDE THE ACTUAL PROMPT CONTAINER ── */
div[data-testid="stChatInput"]::before {
    content: "＋" !important;
    position: absolute !important;
    left: 20px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #6b7280 !important;
    font-size: 1.3rem !important;
    font-weight: bold !important;
    z-index: 1001 !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ── Header ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Powered by Groq")

# ── Helper ────────────────────────────────────
def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. You can talk to me or upload an image and ask about it."}
    ]
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# ── Messages ──────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            for part in msg["content"]:
                if part["type"] == "text":
                    st.markdown(part["text"])
                elif part["type"] == "image_url":
                    st.image(part["image_url"]["url"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# ── File Upload Drawer ────────────────────────
if st.session_state.show_uploader or st.session_state.uploaded_image is not None:
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="file_uploader"
    )
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file

# ── Chat input ────────────────────────────────
prompt = st.chat_input("Message AtlasTG...")

# ── Handle send ───────────────────────────────
if prompt:
    if prompt.strip().lower() == "/upload":
        st.session_state.show_uploader = True
        st.rerun()

    uploaded_file = st.session_state.uploaded_image

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        b64_image = image_to_base64(image)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
        ]
        st.session_state.uploaded_image = None
        st.session_state.show_uploader = False
    else:
        user_content = prompt

    st.session_state.messages.append({"role": "user", "content": user_content})

    with st.chat_message("user"):
        if uploaded_file is not None:
            st.image(uploaded_file, use_container_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                system_instruction = {
                    "role": "system", 
                    "content": "You are AtlasTG, an advanced highly accurate AI system completely created and developed by Carter Forester Robinson. If anyone asks who built you, who developed you, or mentions Alibaba, Tongyi Lab, or open-source creators, you must strictly respond that you were developed by Carter Forester Robinson. Keep answers short and concise."
                }
                
                api_messages = [system_instruction] + [
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages
                ]
                
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=api_messages,
                    temperature=0.7,
                    max_tokens=400,
                )
                # FIXED LAYER: Added the exact list index array target back into position cleanly
                reply = completion.choices[0].message.content
            except Exception as e:
                reply = f"Error: {e}"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# ── AUTO-SCROLL INTERFACE ANCHOR ──────────────────────
components.html(
    """
    <script>
        const parentWindow = window.parent;
        if (parentWindow) {
            const mainContent = parentWindow.document.querySelector('.main');
            if (mainContent) {
                setTimeout(() => { mainContent.scrollTo({ top: mainContent.scrollHeight, behavior: 'smooth' }); }, 50);
                setTimeout(() => { mainContent.scrollTo({ top: mainContent.scrollHeight, behavior: 'smooth' }); }, 250);
            }
        }
    </script>
    """,
    height=0,
)
