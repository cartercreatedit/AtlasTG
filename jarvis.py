import streamlit as st
from groq import Groq
import datetime
import base64
import html
import streamlit.components.v1 as components

# ============================================================
# J.A.R.V.I.S.
# Voice conversation version
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# GROQ
# ============================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = ""

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

# ============================================================
# MEMORY
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "listening" not in st.session_state:
    st.session_state.listening = False

if "speak_text" not in st.session_state:
    st.session_state.speak_text = ""

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    background: #0a0a0a !important;
}

.stApp {
    background: #0a0a0a;
    color: white;
}

.block-container {
    max-width: 760px;
    padding-top: 35px;
}

/* TITLE */

.jarvis-title {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 8px;
}

.jarvis-subtitle {
    text-align: center;
    color: #666;
    letter-spacing: 3px;
    margin-bottom: 25px;
}

/* CORE */

.core-container {
    display: flex;
    justify-content: center;
    margin: 15px 0 20px 0;
}

.core {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 2px solid #00f2fe;

    display: flex;
    align-items: center;
    justify-content: center;

    box-shadow:
        0 0 15px #00f2fe,
        0 0 40px rgba(0,242,254,.25),
        inset 0 0 25px rgba(0,242,254,.15);
}

.inner-core {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    border: 2px solid #00f2fe;

    box-shadow:
        0 0 15px #00f2fe,
        inset 0 0 20px rgba(0,242,254,.25);
}

/* BUTTONS */

div.stButton > button {
    border-radius: 14px;
    height: 48px;
    background: #151515;
    border: 1px solid #333;
    color: white;
}

div.stButton > button:hover {
    border-color: #00f2fe;
    color: #00f2fe;
}

/* HIDE AUDIO INPUT LABEL */

div[data-testid="stAudioInput"] label {
    display: none;
}

/* CHAT */

.chat {
    background: #111;
    border: 1px solid #222;
    border-radius: 14px;
    padding: 15px;
    margin: 10px 0;
}

.user {
    color: #00f2fe;
}

.jarvis {
    color: white;
}

.status {
    text-align: center;
    color: #777;
    font-size: 13px;
    margin: 15px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# TIME
# ============================================================

now = datetime.datetime.now()

current_time = now.strftime("%I:%M %p")
current_date = now.strftime("%A, %B %d, %Y")

# ============================================================
# SPEECH FUNCTION
# ============================================================

def browser_speak(text):

    safe_text = html.escape(text)

    components.html(
        f"""
        <script>
        const text = {json_string(safe_text)};

        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();

            const speech = new SpeechSynthesisUtterance(text);

            speech.rate = 0.95;
            speech.pitch = 0.9;
            speech.volume = 1.0;

            window.speechSynthesis.speak(speech);
        }}
        </script>
        """,
        height=1
    )


def json_string(text):
    import json
    return json.dumps(text)


# ============================================================
# TRANSCRIPTION
# ============================================================

def transcribe_audio(audio):

    if not client:
        return None

    try:

        result = client.audio.transcriptions.create(
            file=(
                "voice.wav",
                audio.getvalue()
            ),
            model="whisper-large-v3-turbo",
            response_format="json"
        )

        return result.text

    except Exception as e:

        st.error(f"Microphone error: {e}")
        return None


# ============================================================
# JARVIS AI
# ============================================================

def ask_jarvis(user_text):

    if not client:
        return "My Groq API key isn't connected."

    system = f"""
You are J.A.R.V.I.S., a personal AI assistant.

Current date:
{current_date}

Current time:
{current_time}

The user is having a spoken conversation with you.

Respond naturally and conversationally.

The user may speak different languages.
Reply in the same language the user is speaking.

Keep answers reasonably concise because they will be
spoken aloud.

You can answer questions and help with tasks.

Never claim that you performed a computer action unless
the application actually performed it.
"""

    messages = [
        {
            "role": "system",
            "content": system
        }
    ]

    messages.extend(
        st.session_state.messages[-12:]
    )

    messages.append(
        {
            "role": "user",
            "content": user_text
        }
    )

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"I encountered an error: {e}"


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="jarvis-title">J.A.R.V.I.S.</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="jarvis-subtitle">PERSONAL AI SYSTEM</div>',
    unsafe_allow_html=True
)

# ============================================================
# CORE
# ============================================================

st.markdown("""
<div class="core-container">
    <div class="core">
        <div class="inner-core"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN CONTROLS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    if st.button("◉ TALK", use_container_width=True):

        st.session_state.listening = True
        st.rerun()

with col2:

    if st.button("TIME", use_container_width=True):

        answer = f"The current time is {current_time}."

        st.session_state.messages.append({
            "role": "user",
            "content": "What time is it?"
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.session_state.speak_text = answer

        st.rerun()

with col3:

    if st.button("CLEAR", use_container_width=True):

        st.session_state.messages = []
        st.session_state.speak_text = ""

        st.rerun()

# ============================================================
# MICROPHONE
# ============================================================

if st.session_state.listening:

    st.markdown(
        '<div class="status">🎙️ Listening — speak now</div>',
        unsafe_allow_html=True
    )

    audio = st.audio_input(
        "Microphone",
        sample_rate=16000,
        label_visibility="collapsed"
    )

    if audio:

        spoken_text = transcribe_audio(audio)

        st.session_state.listening = False

        if spoken_text:

            st.session_state.messages.append({
                "role": "user",
                "content": spoken_text
            })

            answer = ask_jarvis(spoken_text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            st.session_state.speak_text = answer

        st.rerun()

# ============================================================
# CHAT
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="chat user">
                <b>You:</b> {html.escape(message["content"])}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="chat jarvis">
                <b>J.A.R.V.I.S.:</b> {html.escape(message["content"])}
            </div>
            """,
            unsafe_allow_html=True
        )

# ============================================================
# SPEAK LAST RESPONSE
# ============================================================

if st.session_state.speak_text:

    browser_speak(
        st.session_state.speak_text
    )

    st.session_state.speak_text = ""

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="status">GROQ • VOICE CONVERSATION • MULTILINGUAL</div>',
    unsafe_allow_html=True
)
