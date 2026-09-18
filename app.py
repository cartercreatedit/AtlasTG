import streamlit as st
from groq import Groq
import os

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
/* Pure dark background */
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}

.main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 6rem;
    max-width: 760px;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden;
}

/* Title */
h1 {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.15rem !important;
}

.stCaption {
    color: #8b8b8b !important;
    font-size: 0.9rem !important;
}

/* ========== HIDE AVATARS ========== */
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"],
.stChatMessage [data-testid="stImage"] {
    display: none !important;
}

/* Remove left padding that was reserved for avatars */
.stChatMessage {
    background-color: transparent !important;
    border: none !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 0.75rem !important;
    padding-bottom: 0.75rem !important;
}

/* Make messages full width like this site */
.stChatMessage > div {
    max-width: 100% !important;
}

/* User message styling */
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: transparent !important;
}

/* Text styling */
div[data-testid="stMarkdownContainer"] p {
    color: #e8e8e8 !important;
    line-height: 1.65 !important;
    font-size: 1.05rem !important;
    margin-bottom: 0.3rem !important;
}

/* Chat input */
.stChatInput {
    background-color: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 18px !important;
}

.stChatInput textarea {
    color: #e8e8e8 !important;
    background-color: transparent !important;
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
st.caption("Powered by Groq")

# ── Chat history ──────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. What do you want to talk about?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────
if prompt := st.chat_input("Message AtlasTG..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=1024,
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"Error: {e}"

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
