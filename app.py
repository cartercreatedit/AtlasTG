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

# ── ORIGINAL BORDERLESS GOOGLE-STYLE STYLING ─────────────────────────
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

/* Force clean text behavior inside all markdown elements */
div[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
}

/* ── USER PROMPT POINTED BUBBLES ── */
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
    border-top-right-radius: 2px !important; /* Pointed sharp tail top right secured */
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

/* ── PREMIUM BORDERLESS MIDNIGHT TEXT BOX (NO WHITE RING HIGHLIGHT) ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #161616 !important;
    border: none !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 20px !important; 
}
.stChatInput:focus-within {
    border: none !important;
    box-shadow: 0 4px 35px rgba(0,0,0,0.6) !important;
    outline: none !important;
}

/* Obliterate inner background border constraints */
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

# ── Render Message Timeline using Native Safe Structures ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                    {msg["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── SINGLE TEXT INPUT CONSOLE DOCK ─────────────────────
text_prompt = st.chat_input("Message AtlasTG...")

# ── PROCESS INJECTED PARAMETERS ──────────────────────
if text_prompt:
    st.session_state.messages.append({"role": "user", "content": text_prompt})
    
    with st.spinner(""):
        try:
            # FIXED IDENTITY MATRIX VALUE OVERRIDE LOCK
            sys_content = (
                "You are AtlasTG, an advanced, high-precision artificial intelligence engine. "
                "You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. "
                "CRITICAL TIMELINE AND IDENTITY LAWS: "
                "1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation. "
                "2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix. "
                "3. Your conversational style emulates the highest standards of logical depth, emotional clarity, and technical sophistication. "
                "FORMATTING LAWS: "
                "- NEVER use Markdown or HTML tables under any circumstances. "
                "- Structure information visually using Markdown headers (###), bold tags, and bullet points. "
                "- Dynamically scale response lengths. Keep greetings or casual phrases concise, but expand deeply into structured paragraphs for complex logic, emotional scenarios, or relationship questions."
            )
            api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b", 
                messages=api_messages, 
                temperature=0.2, 
                max_tokens=1000
            )
            # FIXED UNPACKING INDEX BLOCK HERE
            reply = completion.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
            
    st.rerun()

# ── SAFE AUTO-SCROLL INTERFACE ANCHOR ──────────────────────
scroll_js = "<script>const main = window.parent.document.querySelector('.main'); if(main){ setTimeout(() => { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }, 50); }</script>"
components.html(scroll_js, height=0)
