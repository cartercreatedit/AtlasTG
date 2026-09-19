import streamlit as st
from groq import Groq
import os
import base64
import tempfile
import requests
import time

# ============================================================
# J.A.R.V.I.S. - VOICE ASSISTANT
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# API KEYS
# ============================================================

groq_key = (
    st.secrets.get("GROQ_API_KEY", "")
    or os.getenv("GROQ_API_KEY", "")
)

eleven_key = (
    st.secrets.get("ELEVEN_API_KEY", "")
    or os.getenv("ELEVEN_API_KEY", "")
)

voice_id = (
    st.secrets.get("ELEVEN_VOICE_ID", "")
    or os.getenv("ELEVEN_VOICE_ID", "")
)

if not groq_key:
    st.error("Missing GROQ_API_KEY.")
    st.stop()

if not eleven_key:
    st.error("Missing ELEVEN_API_KEY.")
    st.stop()

if not voice_id:
    st.error("Missing ELEVEN_VOICE_ID.")
    st.stop()

client = Groq(api_key=groq_key)

# ============================================================
# CONVERSATION MEMORY
# ============================================================

if "vox_history" not in st.session_state:
    st.session_state.vox_history = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a highly advanced AI assistant "
                "created by Carter Forester-Robinson. "
                "Address Carter as sir or Mr. Robinson. "
                "Your personality is intelligent, calm, professional, "
                "loyal, sophisticated and slightly witty. "
                "Keep spoken responses short and natural, usually "
                "one to three sentences. "
                "Do not use markdown, lists, emojis or headings."
            ),
        }
    ]

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ============================================================
# PAGE STYLE
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #000000 !important;
    }

    header {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# JARVIS UI
# ============================================================

st.markdown(
    """
    <div style="
        width:100%;
        min-height:55vh;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        background:#000;
    ">

        <div style="
            width:170px;
            height:170px;
            border-radius:50%;
            border:2px solid #00f2fe;
            box-shadow:
                0 0 25px rgba(0,242,254,.35),
                0 0 70px rgba(0,242,254,.12),
                inset 0 0 30px rgba(0,242,254,.15);
            display:flex;
            align-items:center;
            justify-content:center;
            animation:pulse 3s infinite ease-in-out;
        ">

            <div style="
                width:105px;
                height:105px;
                border-radius:50%;
                border:1px solid rgba(0,242,254,.65);
                box-shadow:
                    0 0 25px rgba(0,242,254,.4),
                    inset 0 0 25px rgba(0,242,254,.12);
                display:flex;
                align-items:center;
                justify-content:center;
                color:#00f2fe;
                font-size:42px;
            ">
                ✦
            </div>

        </div>

        <div style="
            margin-top:30px;
            color:#00f2fe;
            font-family:Arial,sans-serif;
            font-size:13px;
            letter-spacing:3px;
            opacity:.75;
        ">
            J.A.R.V.I.S.
        </div>

        <div style="
            margin-top:10px;
            color:#777;
            font-family:Arial,sans-serif;
            font-size:11px;
            letter-spacing:2px;
        ">
            VOICE CORE ONLINE
        </div>

    </div>

    <style>

    @keyframes pulse {
        0% {
            transform:scale(1);
        }

        50% {
            transform:scale(1.035);
        }

        100% {
            transform:scale(1);
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# MICROPHONE
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#777;
        font-family:Arial,sans-serif;
        font-size:12px;
        letter-spacing:1px;
        margin-bottom:10px;
    ">
        TAP THE MICROPHONE AND SPEAK
    </div>
    """,
    unsafe_allow_html=True,
)

audio_input = st.audio_input(
    "Speak to J.A.R.V.I.S.",
    key="jarvis_microphone",
)

# ============================================================
# PROCESS AUDIO
# ============================================================

if audio_input is not None:

    # Give every recording a unique ID.
    audio_bytes = audio_input.getvalue()
    audio_id = str(hash(audio_bytes))

    # Prevent Streamlit from processing the exact same recording again.
    if audio_id != st.session_state.last_audio_id:

        st.session_state.last_audio_id = audio_id

        try:

            # ------------------------------------------------
            # SAVE RECORDING
            # ------------------------------------------------

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as temp_audio:

                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name

            # ------------------------------------------------
            # SPEECH TO TEXT
            # ------------------------------------------------

            with open(
                temp_audio_path,
                "rb"
            ) as audio_file:

                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    response_format="text",
                )

            # ------------------------------------------------
            # DELETE TEMP FILE
            # ------------------------------------------------

            try:
                os.remove(temp_audio_path)
            except OSError:
                pass

            # ------------------------------------------------
            # GET TEXT
            # ------------------------------------------------

            if isinstance(transcription, str):

                user_text = transcription.strip()

            else:

                user_text = str(
                    getattr(
                        transcription,
                        "text",
                        transcription
                    )
                ).strip()

            if not user_text:

                st.warning(
                    "I didn't hear anything, sir."
                )

                st.stop()

            # ------------------------------------------------
            # ADD USER MESSAGE
            # ------------------------------------------------

            st.session_state.vox_history.append(
                {
                    "role": "user",
                    "content": user_text,
                }
            )

            # ------------------------------------------------
            # GROQ AI RESPONSE
            # ------------------------------------------------

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.vox_history[-10:],
                temperature=0.3,
                max_tokens=200,
            )

            reply = (
                completion
                .choices[0]
                .message
                .content
                .strip()
            )

            # ------------------------------------------------
            # SAVE ASSISTANT RESPONSE
            # ------------------------------------------------

            st.session_state.vox_history.append(
                {
                    "role": "assistant",
                    "content": reply,
                }
            )

            # ------------------------------------------------
            # ELEVENLABS TEXT TO SPEECH
            # ------------------------------------------------

            tts_url = (
                "https://api.elevenlabs.io/v1/"
                "text-to-speech/"
                + voice_id
            )

            headers = {
                "xi-api-key": eleven_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }

            payload = {
                "text": reply,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.85,
                },
            }

            tts_response = requests.post(
                tts_url,
                headers=headers,
                json=payload,
                timeout=60,
            )

            # ------------------------------------------------
            # CHECK ELEVENLABS RESPONSE
            # ------------------------------------------------

            if not tts_response.ok:

                st.error(
                    "ElevenLabs error: "
                    + tts_response.text[:500]
                )

                st.stop()

            # ------------------------------------------------
            # CONVERT AUDIO TO BASE64
            # ------------------------------------------------

            audio_base64 = base64.b64encode(
                tts_response.content
            ).decode("utf-8")

            # ------------------------------------------------
            # PLAY RESPONSE
            # ------------------------------------------------

            st.markdown(
                f"""
                <audio
                    autoplay
                    controls
                    style="
                        width:100%;
                        max-width:500px;
                        margin:20px auto;
                        display:block;
                    "
                >
                    <source
                        src="data:audio/mpeg;base64,{audio_base64}"
                        type="audio/mpeg"
                    >
                </audio>
                """,
                unsafe_allow_html=True,
            )

            # ------------------------------------------------
            # SHOW WHAT WAS SAID
            # ------------------------------------------------

            st.markdown(
                f"""
                <div style="
                    background:#050505;
                    border:1px solid #111;
                    border-radius:12px;
                    padding:15px;
                    margin:15px auto;
                    max-width:500px;
                    font-family:Arial,sans-serif;
                ">

                    <div style="
                        color:#555;
                        font-size:10px;
                        letter-spacing:2px;
                        margin-bottom:7px;
                    ">
                        YOU
                    </div>

                    <div style="
                        color:#aaa;
                        font-size:14px;
                    ">
                        {user_text}
                    </div>

                    <div style="
                        color:#555;
                        font-size:10px;
                        letter-spacing:2px;
                        margin-top:15px;
                        margin-bottom:7px;
                    ">
                        J.A.R.V.I.S.
                    </div>

                    <div style="
                        color:#00f2fe;
                        font-size:14px;
                    ">
                        {reply}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        except Exception as error:

            st.error(
                "J.A.R.V.I.S. processing error: "
                + str(error)
            )

# ============================================================
# RESET BUTTON
# ============================================================

st.markdown(
    "<br>",
    unsafe_allow_html=True,
)

if st.button(
    "RESET CONVERSATION",
    use_container_width=True
):

    st.session_state.vox_history = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a highly advanced AI assistant "
                "created by Carter Forester-Robinson. "
                "Address Carter as sir or Mr. Robinson. "
                "Your personality is intelligent, calm, professional, "
                "loyal, sophisticated and slightly witty. "
                "Keep spoken responses short and natural, usually "
                "one to three sentences. "
                "Do not use markdown, lists, emojis or headings."
            ),
        }
    ]

    st.session_state.last_audio_id = None

    st.rerun()
