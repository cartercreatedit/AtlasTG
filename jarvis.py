import streamlit as st
from groq import Groq
import datetime
import base64
import requests

# ============================================================
# J.A.R.V.I.S.
# Voice Input + AI + Voice Output
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered"
)

# ============================================================
# API KEY
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
# STYLE
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
    padding-top: 40px;
}

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
    margin-bottom: 35px;
}

.core {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 2px solid #00f2fe;
    margin: 20px auto 40px auto;

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

.chat {
    background: #111;
    border: 1px solid #222;
    border-radius: 14px;
    padding: 16px;
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
    color: #666;
    font-size: 13px;
    margin: 15px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# ============================================================
# FUNCTIONS
# ============================================================

def get_time():
    return datetime.datetime.now().strftime("%I:%M %p")


def get_date():
    return datetime.datetime.now().strftime("%A, %B %d, %Y")


def transcribe_audio(audio_file):

    if not client:
        return None

    try:

        transcription = client.audio.transcriptions.create(
            file=(
                "voice.wav",
                audio_file.getvalue()
            ),
            model="whisper-large-v3-turbo",
            response_format="json"
        )

        return transcription.text

    except Exception as e:

        st.error(f"Speech recognition error: {e}")
        return None


def ask_jarvis(text):

    if not client:
        return "My Groq API key isn't connected yet."

    system_prompt = f"""
You are J.A.R.V.I.S., a personal AI assistant.

Current date:
{get_date()}

Current time:
{get_time()}

You can communicate in many languages.

Reply in the same language the user speaks unless they
specifically request another language.

Be natural, intelligent and helpful.

Keep normal answers reasonably concise because your
responses will be spoken aloud.

Do not claim that you performed an action unless you
actually performed it.

The current application can receive voice input and
produce spoken output.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(
        st.session_state.messages[-12:]
    )

    messages.append(
        {
            "role": "user",
            "content": text
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


def text_to_speech(text):

    if not GROQ_API_KEY:
        return None

    try:

        # Groq's Orpheus endpoint currently limits input to 200 characters.
        short_text = text[:200]

        response = requests.post(
            "https://api.groq.com/openai/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "canopylabs/orpheus-v1-english",
                "voice": "troy",
                "input": short_text,
                "response_format": "wav"
            },
            timeout=60
        )

        if response.status_code != 200:
            st.error(
                f"Voice generation error: "
                f"{response.status_code} {response.text}"
            )
            return None

        return response.content

    except Exception as e:

        st.error(f"Voice generation error: {e}")
        return None


def play_audio(audio_bytes):

    if audio_bytes:

        audio_base64 = base64.b64encode(
            audio_bytes
        ).decode()

        audio_html = f"""
        <audio autoplay controls>
            <source
                src="data:audio/wav;base64,{audio_base64}"
                type="audio/wav"
            >
        </audio>
        """

        st.markdown(
            audio_html,
            unsafe_allow_html=True
        )


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
<div class="core">
    <div class="inner-core"></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# QUICK BUTTONS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    if st.button("TIME", use_container_width=True):

        answer = f"The current time is {get_time()}."

        st.session_state.messages.append({
            "role": "user",
            "content": "What time is it?"
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        audio = text_to_speech(answer)

        st.session_state.last_audio = audio

        st.rerun()


with col2:

    if st.button("DATE", use_container_width=True):

        answer = f"Today is {get_date()}."

        st.session_state.messages.append({
            "role": "user",
            "content": "What is today's date?"
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        audio = text_to_speech(answer)

        st.session_state.last_audio = audio

        st.rerun()


with col3:

    if st.button("CLEAR", use_container_width=True):

        st.session_state.messages = []
        st.session_state.last_audio = None

        st.rerun()

# ============================================================
# MICROPHONE
# ============================================================

st.markdown(
    '<div class="status">🎙️ Press the microphone and speak</div>',
    unsafe_allow_html=True
)

audio_input = st.audio_input(
    "Talk to J.A.R.V.I.S.",
    sample_rate=16000
)

# ============================================================
# PROCESS VOICE
# ============================================================

if audio_input:

    spoken_text = transcribe_audio(audio_input)

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

        audio_reply = text_to_speech(answer)

        st.session_state.last_audio = audio_reply

        st.rerun()

# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="chat user">
                <b>You:</b> {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="chat jarvis">
                <b>J.A.R.V.I.S.:</b> {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

# ============================================================
# PLAY LAST RESPONSE
# ============================================================

if st.session_state.last_audio:

    st.markdown(
        '<div class="status">🔊 J.A.R.V.I.S. speaking...</div>',
        unsafe_allow_html=True
    )

    play_audio(
        st.session_state.last_audio
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="status">GROQ • VOICE • MULTILINGUAL • J.A.R.V.I.S.</div>',
    unsafe_allow_html=True
)
