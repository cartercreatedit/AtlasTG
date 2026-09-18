import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
import io
import streamlit.components.v1 as components # Added the component helper

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
    padding-bottom: 140px !important;
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

/* Hide avatars */
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {
    display: none !important;
}
.stChatMessage {
    background-color: transparent !important;
    border: none !important;
    padding-left: 0 !important;
}

/* Sticky input */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 20px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 24px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}
.stChatInput textarea {
    color: #e8e8e8 !important;
}

/* Round + button */
div.stButton > button {
    background-color: #1a1a1a !important;
    border: 1px solid #2f2f2f !important;
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    padding: 0 !important;
    color: #e8e8e8 !important;
    font-size: 1.5rem !important;
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
st.caption("Text + Image Understanding · Powered by Groq")

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

# ── Bottom controls ───────────────────────────
col_plus, col_input = st.columns([0.07, 0.93], gap="small")

with col_plus:
    if st.button("＋", key="plus_btn"):
        st.session_state.show_uploader = not st.session_state.show_uploader

with col_input:
    prompt = st.chat_input("Message AtlasTG...")

if st.session_state.show_uploader:
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="file_uploader"
    )
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file
        st.session_state.show_uploader = False
        st.rerun()

# ── Handle send ───────────────────────────────
if prompt:
    uploaded_file = st.session_state.uploaded_image

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        b64_image = image_to_base64(image)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
        ]
        st.session_state.uploaded_image = None
    else:
        user_content = prompt

    st.session_state.messages.append({"role": "user", "content": user_content})

    with st.chat_message("user"):
        if uploaded_file is not None:
            st.image(uploaded_file, use_container_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            completion = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=api_messages,
                temperature=0.7,
                max_tokens=1024,
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"Error: {e}"

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ── FIXED AUTO-SCROLL INTERFACE ANCHOR ────────
# This targets parent document nodes outside the local sandboxed iframe to lock viewport alignment
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
