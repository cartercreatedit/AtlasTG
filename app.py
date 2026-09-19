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

# ── Identity Rules ────────────────────────────
sys_content = """You are AtlasTG, an advanced, high-precision artificial intelligence engine. You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. CRITICAL TIMELINE AND IDENTITY LAWS: 1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation. 2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix. 3. Your conversational style emulates the highest standards of logical depth and emotionless precision."""

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Ask me any text prompt or logic question and I will solve it instantly. You can also attach images."}
    ]

# ── Render Message Timeline ───────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        if isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, list):
            for part in content:
                if part["type"] == "text":
                    st.markdown(part["text"])
        
        if "images" in msg and msg["images"]:
            for img_bytes in msg["images"]:
                st.image(img_bytes, width=280)

# ── CHAT INPUT WITH IMAGE UPLOAD ──────────────
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
        resolved_text = user_text if user_text.strip() else "Analyze this image."
        content_payload = [{"type": "text", "text": resolved_text}]
        
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
        
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-instruct",
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
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()
