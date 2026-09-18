import streamlit as st
from groq import Groq
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

# ── CSS + Auto-Scroll ─────────────────────────
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

<script>
// Function to scroll the Streamlit container, not the window
function scrollToBottom() {
    const container = document.querySelector('div[data-testid="stMainBlockContainer"]');
    if (container) {
        // Check if user is near the bottom (within 100px)
        const isNearBottom = (container.scrollHeight - container.scrollTop - container.clientHeight) < 100;
        if (isNearBottom) {
            container.scrollTop = container.scrollHeight;
        }
    }
}

// Observe changes to the DOM and scroll if content is added
const observer = new MutationObserver(scrollToBottom);
const targetNode = document.querySelector('div[data-testid="stMainBlockContainer"]');

if (targetNode) {
    observer.observe(targetNode, { childList: true, subtree: true });
}

// Initial scroll
setTimeout(scrollToBottom, 100);
</script>
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
