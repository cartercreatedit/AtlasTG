import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
import io

# ── Page config ───────────────────────────────
st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── AtlasTG / Grok-style CSS ──────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 8rem;
    max-width: 760px;
}
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden;
}
h1 {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.15rem !important;
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
    padding-right: 0 !important;
}
div[data-testid="stMarkdownContainer"] p {
    color: #e8e8e8 !important;
    line-height: 1.65 !important;
    font-size: 1.05rem !important;
}

/* Chat input */
.stChatInput {
    background-color: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 24px !important;
}
.stChatInput textarea {
    color: #e8e8e8 !important;
}

/* ========== Grok-style + button ========== */
div[data-testid="stFileUploader"] {
    padding: 0 !important;
    margin: 0 !important;
}
div[data-testid="stFileUploader"] > section {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}
div[data-testid="stFileUploader"] label {
    display: none !important;
}
div[data-testid="stFileUploader"] button {
    background-color: #1a1a1a !important;
    border: 1px solid #2f2f2f !important;
    border-radius: 50% !important;          /* round like Grok */
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    padding: 0 !important;
    color: #e8e8e8 !important;
    font-size: 1.4rem !important;
    font-weight: 300 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
div[data-testid="stFileUploader"] button:hover {
    background-color: #252525 !important;
    border-color: #3a3a3a !important;
}
div[data-testid="stFileUploader"] button p {
    margin: 0 !important;
    font-size: 1.4rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY — add it in Streamlit Secrets")
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

# ── Chat history ──────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. You can talk to me or upload an image and ask about it."}
    ]

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

# ── Bottom bar: + button + chat input ─────────
col_plus, col_input = st.columns([0.07, 0.93], gap="small")

with col_plus:
    uploaded_file = st.file_uploader(
        "+",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
        key="image_uploader"
    )

with col_input:
    prompt = st.chat_input("Message AtlasTG...")

# ── Handle message ────────────────────────────
if prompt:
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        b64_image = image_to_base64(image)

        user_content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_image}"
                }
            }
        ]
    else:
        user_content = prompt

    st.session_state.messages.append({"role": "user", "content": user_content})

    with st.chat_message("user"):
        if uploaded_file is not None:
            st.image(uploaded_file, use_container_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            completion = client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=api_messages,
                temperature=0.7,
                max_tokens=1024,
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"Error: {e}"

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
