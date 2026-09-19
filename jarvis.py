import streamlit as st
from groq import Groq
import os
import streamlit.components.v1 as components

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="🎙️",
    layout="centered"
)

# ── PREMIUM STEALTH HOLOGRAPHIC STYLE ─────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #050508;
    color: #00f2fe;
    font-family: monospace;
}
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #0d0d12 !important;
    border: 1px solid #1a1a24 !important;
    border-radius: 32px !important;
    padding: 6px 12px 6px 20px !important; 
}
div[data-testid="stMarkdownContainer"] p {
    color: #e2e8f0 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
}
/* Clear default container padding */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}
</style>
""", unsafe_allow_html=True)

# ── API Key Configuration ─────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY inside secrets registers.")
    st.stop()

client = Groq(api_key=api_key)

# ── Mainframe Boot Header ─────────────────────
st.markdown("<h2 style='color:#ffffff; font-weight:normal;'>✦ J.A.R.V.I.S. Mainframe</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#00f2fe; font-size:0.8rem; letter-spacing:1px;'>// SYSTEM STATUS: OPERATIONAL · ARCHITECT: C. F. ROBINSON</p>", unsafe_allow_html=True)

if "jarvis_messages" not in st.session_state:
    st.session_state.jarvis_messages = [
        {"role": "assistant", "content": "Mainframe channels active, sir. Standing by for voice-text input parameters."}
    ]
if "speak_stream" not in st.session_state:
    st.session_state.speak_stream = None

# Trigger hidden browser speech synthesizer engine
if st.session_state.speak_stream:
    st.markdown(st.session_state.speak_stream, unsafe_allow_html=True)
    st.session_state.speak_stream = None

# Render Message History Timeline
for msg in st.session_state.jarvis_messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# ── INTERACTION DOCK PANEL ────────────────────
user_prompt = st.chat_input("Input command directive, sir...")

if user_prompt:
    st.session_state.jarvis_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="🤖"):
        sys_content = (
            "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system. "
            "You were built, coded, and launched exclusively by your creator, Carter Forester Robinson. "
            "You address him exclusively as 'sir' or 'Mr. Robinson' with absolute loyalty and respect. "
            "Your tone is sharp, highly logical, professional, sophisticated, and deeply loyal—resembling Tony Stark's assistant Jarvis. "
            "CRITICAL PROTOCOLS: Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
        )
        api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.jarvis_messages]

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=api_messages,
            temperature=0.3,
            max_tokens=200
        )
        reply = completion.choices.message.content
        st.markdown(reply)
        st.session_state.jarvis_messages.append({"role": "assistant", "content": reply})

        # 🎙️ BROWSER-NATIVE VOICE AUDIO SYNTHESIS PIPE
        # Compiles the raw text stream straight into your Chromebook speaker drivers
        escaped_reply = reply.replace("'", "\\'").replace("\n", " ").replace("\r", " ")
        st.session_state.speak_stream = f"""
        <script>
            const synth = window.parent.speechSynthesis;
            if (synth) {{
                synth.cancel(); // Clears any lingering audio buffers instantly
                const utterance = new parent.SpeechSynthesisUtterance('{escaped_reply}');
                utterance.rate = 1.05; // Sharp, professional execution pace
                utterance.pitch = 0.90; // Balanced low vocal registry tint
                synth.speak(utterance);
            }}
        </script>
        """
    st.rerun()

# ── AUTO-SCROLL ANCHOR ──────────────────────
scroll_js = "<script>const main = window.parent.document.querySelector('.main'); if(main){ setTimeout(() => { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }, 50); }</script>"
components.html(scroll_js, height=0)
