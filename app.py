import streamlit as st
from groq import Groq
import os

# ── Page config ───────────────────────────────
st.set_page_config(
    page_title="Grok",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Grok-style CSS ────────────────────────────
st.markdown("""
<style>
/* Pure dark background like Grok */
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}

.main .block-container {
    padding-top: 3rem;
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
    font-size: 1.8rem !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem !important;
}

/* Caption */
.stCaption {
    color: #8b8b8b !important;
    font-size: 0.9rem !important;
}

/* Chat messages */
.stChatMessage {
    background-color: transparent !important;
    border: none !important;
    padding: 0.6rem 0 !important;
}

/* User message bubble */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    background-color: transparent !important;
}

/* Make the chat input look more like Grok */
.stChatInput {
    background-color: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 16px !important;
}

.stChatInput textarea {
    color: #e8e8e8 !important;
    background-color: transparent !important;
}

/* Soften the avatar circles */
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
}

/* Markdown text */
div[data-testid="stMarkdownContainer"] p {
    color: #e8e8e8 !important;
    line-height: 1.6 !important;
    font-size: 1.02rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ── Header (Grok style) ───────────────────────
st.markdown("<h1>Grok</h1>", unsafe_allow_html=True)
st.caption("Built with Groq · openai/gpt-oss-20b")

# ── Chat history ──────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. What do you want to talk about?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────
if prompt := st.chat_input("Message Grok..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get reply
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
