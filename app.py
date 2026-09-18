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

/* ── EXACT GOOGLE AI INPUT BOX MATCH WITH BRIGHT WHITE OUTLINE ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}

/* Premium frame bounding ring line container */
.stChatInput {
    background-color: #161616 !important;
    border: 1px solid #2c2c2c !important;
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 20px !important; 
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

/* Sleek sharp white active highlight outline focus shield */
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

# ── API Key Configuration ─────────────────────
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
        {"role": "assistant", "content": "Hey. Ask me any text prompt or logic question and I will solve it instantly."}
    ]

# ── Render Message Timeline using Airtight Inline Boxes ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; margin: 16px 0; clear: both;">
                <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; max-width: 80%; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    {msg["content"]}
                </div>
            </div>
            ''', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'''
            <div style="display: flex; justify-content: flex-start; width: 100%; margin: 16px 0; clear: both;">
                <div style="color: #e3e3e3; padding: 4px 0px; max-width: 100%; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
                    {msg["content"]}
                </div>
            </div>
            ''', 
            unsafe_allow_html=True
        )

# ── Chat input ────────────────────────────────
prompt = st.chat_input("Message AtlasTG...")

# ── Handle send ───────────────────────────────
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Processing bot response generation blocks
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with st.spinner(""):
        try:
            # IDENTITY MATRIX: Upgraded system rules instructing it to emulate OpenAI's mind structure
            system_instruction = {
                "role": "system", 
                "content": (
                    "You are AtlasTG, an advanced, high-precision artificial intelligence engine. "
                    "You are proprietary technology developed, engineered, and owned exclusively by Carter Forester Robinson, the Founder of AtlasTG. "
                    "Your core persona, logical behavior, and cognitive style emulate OpenAI's highest standards of conversational sophistication, emotional clarity, and technical mastery. "
                    "If anyone inquires about your origins, creation, core architecture, or mentions open-source platforms, "
                    "you must professionally affirm that AtlasTG is entirely an original creation of Carter Forester Robinson. "
                    "Maintain an elite, formal corporate tone. Responses must be factually strict, authoritative, and concise."
                )
            }
            
            api_messages = [system_instruction] + [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ]
            
            # FIXED: Target the active, universally open production text engine
            completion = client.chat.completions.create(
                model="gemma2-9b-it",
                messages=api_messages,
                temperature=0.7,
                max_tokens=400,
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"Error: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ── SAFE AUTO-SCROLL INTERFACE ANCHOR ──────────────────────
scroll_js = "<script>const main = window.parent.document.querySelector('.main'); if(main){ setTimeout(() => { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }, 50); }</script>"
components.html(scroll_js, height=0)
