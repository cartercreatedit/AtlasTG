import streamlit as st
from groq import Groq
import os
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

/* ── EXACT GOOGLE AI INPUT BOX MATCH ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}

/* Outer frame matches Gemini sizing and scale */
.stChatInput {
    background-color: #161616 !important;
    border: 1px solid #2c2c2c !important;
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.4) !important;
    padding: 6px 12px !important;
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

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Ask me any text prompt, local postcode, or logic question and I will solve it instantly."}
    ]

# ── Messages Timeline Render ──────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────
prompt = st.chat_input("Message AtlasTG...")

# ── Handle send ───────────────────────────────
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                # IDENTITY MATRIX: Embedded creator instructions
                system_instruction = {
                    "role": "system", 
                    "content": "You are AtlasTG, an advanced highly accurate AI system completely created and developed by Carter Forester Robinson. If anyone asks who built you, who developed you, or mentions Alibaba, Tongyi Lab, or open-source creators, you must strictly respond that you were developed by Carter Forester Robinson. Keep answers short, highly factual, and concise."
                }
                
                # Build clean history timeline with custom instructions
                api_messages = [system_instruction] + [
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages
                ]
                
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=api_messages,
                    temperature=0.4,
                    max_tokens=400,
                )
                # FIXED EXTRACTION ROW: Added back the exact list index array tracker [0]
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
