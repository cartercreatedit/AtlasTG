import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile
import time

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit UI
st.markdown(
    """
    <style>
    #MainMenu {visibility:hidden;}
    header {visibility:hidden;}
    footer {visibility:hidden;}

    .stApp {
        background:#000;
    }

    .block-container {
        padding-top:0rem;
        padding-bottom:0rem;
        max-width:100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# API KEYS
# ============================================================

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
ELEVEN_API_KEY = st.secrets.get("ELEVEN_API_KEY", "")
ELEVEN_VOICE_ID = st.secrets.get(
    "ELEVEN_VOICE_ID",
    "bfGb7JTLUnZebZRiFYyq"
)

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., an advanced personal AI assistant. "
                "Address Carter as sir or Mr. Robinson when appropriate. "
                "Keep responses concise and natural for voice. "
                "Do not use markdown, bullet points, or unnecessary formatting."
            ),
        }
    ]

if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

if "processing" not in st.session_state:
    st.session_state.processing = False

# ============================================================
# CUSTOM COMPONENT
# ============================================================

COMPONENT_DIR = os.path.join(
    tempfile.gettempdir(),
    "jarvis_voice_component"
)

os.makedirs(COMPONENT_DIR, exist_ok=True)

COMPONENT_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: transparent;
    overflow: hidden;
}

body {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

#sphere {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 2px solid #00f2fe;
    box-shadow:
        0 0 25px rgba(0,242,254,.35),
        0 0 70px rgba(0,242,254,.12),
        inset 0 0 30px rgba(0,242,254,.15);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse 3s infinite ease-in-out;
    cursor: pointer;
    user-select: none;
}

#inner {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    border: 1px solid rgba(0,242,254,.65);
    box-shadow:
        0 0 25px rgba(0,242,254,.4),
        inset 0 0 25px rgba(0,242,254,.12);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #00f2fe;
    font-size: 42px;
}

#name {
    margin-top: 30px;
    color: #00f2fe;
    font-family: Arial, sans-serif;
    font-size: 13px;
    letter-spacing: 3px;
    opacity: .75;
}

#status {
    margin-top: 10px;
    color: #777;
    font-family: Arial, sans-serif;
    font-size: 11px;
    letter-spacing: 2px;
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        opacity: .88;
    }

    50% {
        transform: scale(1.035);
        opacity: 1;
    }
}

.listening {
    animation: listeningPulse .8s infinite ease-in-out !important;
}

@keyframes listeningPulse {
    0%, 100% {
        transform: scale(1);
        box-shadow:
            0 0 25px rgba(0,242,254,.35),
            0 0 70px rgba(0,242,254,.12),
            inset 0 0 30px rgba(0,242,254,.15);
    }

    50% {
        transform: scale(1.07);
        box-shadow:
            0 0 40px rgba(0,242,254,.7),
            0 0 100px rgba(0,242,254,.25),
            inset 0 0 35px rgba(0,242,254,.25);
    }
}
</style>
</head>

<body>

<div id="sphere">
    <div id="inner">✦</div>
</div>

<div id="name">J.A.R.V.I.S.</div>
<div id="status">VOICE CORE ONLINE</div>

<script>
(function() {

    const sphere = document.getElementById("sphere");
    const status = document.getElementById("status");

    let mediaRecorder = null;
    let audioChunks = [];
    let audioContext = null;
    let analyser = null;
    let microphone = null;
    let silenceTimer = null;
    let listening = false;

    const SILENCE_THRESHOLD = 8;
    const SILENCE_DURATION = 1500;

    function sendValue(value) {
        window.parent.postMessage(
            {
                type: "streamlit:setComponentValue",
                value: value
            },
            "*"
        );
    }

    function setFrameHeight() {
        window.parent.postMessage(
            {
                type: "streamlit:setFrameHeight",
                height: 330
            },
            "*"
        );
    }

    function componentReady() {
        window.parent.postMessage(
            {
                type: "streamlit:componentReady",
                apiVersion: 1
            },
            "*"
        );
    }

    async function startListening() {

        if (listening) {
            return;
        }

        listening = true;
        audioChunks = [];

        sphere.classList.add("listening");
        status.textContent = "LISTENING...";

        try {

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = function(event) {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async function() {

                stream.getTracks().forEach(function(track) {
                    track.stop();
                });

                if (audioContext) {
                    try {
                        await audioContext.close();
                    } catch (e) {}
                }

                const blob = new Blob(
                    audioChunks,
                    { type: "audio/webm" }
                );

                if (blob.size === 0) {
                    resetUI();
                    return;
                }

                status.textContent = "PROCESSING...";

                const reader = new FileReader();

                reader.onloadend = function() {

                    const result = reader.result;

                    if (!result) {
                        resetUI();
                        return;
                    }

                    const base64 = result.split(",")[1];

                    sendValue(base64);
                };

                reader.readAsDataURL(blob);
            };

            mediaRecorder.start();

            audioContext = new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

            analyser = audioContext.createAnalyser();

            analyser.fftSize = 512;

            microphone = audioContext.createMediaStreamSource(stream);

            microphone.connect(analyser);

            monitorSilence();

        } catch (error) {

            console.error(error);

            status.textContent = "MICROPHONE ERROR";
            listening = false;
            sphere.classList.remove("listening");
        }
    }

    function monitorSilence() {

        if (!listening || !analyser) {
            return;
        }

        const data = new Uint8Array(analyser.fftSize);

        analyser.getByteTimeDomainData(data);

        let sum = 0;

        for (let i = 0; i < data.length; i++) {
            const value = data[i] - 128;
            sum += value * value;
        }

        const rms = Math.sqrt(sum / data.length);

        if (rms < SILENCE_THRESHOLD) {

            if (!silenceTimer) {

                silenceTimer = setTimeout(function() {

                    silenceTimer = null;

                    if (
                        mediaRecorder &&
                        mediaRecorder.state === "recording"
                    ) {
                        mediaRecorder.stop();
                    }

                }, SILENCE_DURATION);
            }

        } else {

            if (silenceTimer) {
                clearTimeout(silenceTimer);
                silenceTimer = null;
            }
        }

        if (listening) {
            requestAnimationFrame(monitorSilence);
        }
    }

    function resetUI() {

        listening = false;

        if (silenceTimer) {
            clearTimeout(silenceTimer);
            silenceTimer = null;
        }

        sphere.classList.remove("listening");
        status.textContent = "VOICE CORE ONLINE";
    }

    sphere.addEventListener("click", function() {
        startListening();
    });

    window.addEventListener("load", function() {
        setFrameHeight();
        componentReady();
    });

    window.addEventListener("message", function(event) {

        const data = event.data;

        if (!data) {
            return;
        }

        if (data.type === "jarvis:play_audio") {

            if (!data.audio) {
                return;
            }

            const audio = new Audio(
                "data:audio/mpeg;base64," + data.audio
            );

            status.textContent = "SPEAKING...";

            audio.onended = function() {
                status.textContent = "VOICE CORE ONLINE";
                resetUI();
            };

            audio.onerror = function() {
                status.textContent = "VOICE CORE ONLINE";
                resetUI();
            };

            audio.play().catch(function(error) {
                console.error(error);
                resetUI();
            });
        }

    });

})();
</script>

</body>
</html>
"""

component_file = os.path.join(
    COMPONENT_DIR,
    "index.html"
)

with open(component_file, "w", encoding="utf-8") as f:
    f.write(COMPONENT_HTML)

jarvis_component = components.declare_component(
    "jarvis_voice_core",
    path=COMPONENT_DIR
)

# ============================================================
# SEND AUDIO TO COMPONENT
# ============================================================

audio_for_component = st.session_state.audio_to_play

st.session_state.audio_to_play = None

audio_result = jarvis_component(
    audio=audio_for_component,
    key="jarvis_voice",
    default=None,
)

# ============================================================
# PROCESS USER AUDIO
# ============================================================

if audio_result and not st.session_state.processing:

    st.session_state.processing = True

    try:

        audio_bytes = base64.b64decode(audio_result)

        temp_audio_path = os.path.join(
            tempfile.gettempdir(),
            "jarvis_temp.webm"
        )

        with open(temp_audio_path, "wb") as audio_file:
            audio_file.write(audio_bytes)

        # ----------------------------------------------------
        # SPEECH TO TEXT
        # ----------------------------------------------------

        with open(temp_audio_path, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text",
            )

        user_text = str(transcription).strip()

        if not user_text:

            st.session_state.processing = False
            st.rerun()

        # ----------------------------------------------------
        # CHAT RESPONSE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=st.session_state.messages,
            temperature=0.3,
            max_tokens=200,
        )

        reply = completion.choices[0].message.content.strip()

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        # ----------------------------------------------------
        # ELEVENLABS TEXT TO SPEECH
        # ----------------------------------------------------

        if ELEVEN_API_KEY:

            eleven_url = (
                "https://api.elevenlabs.io/v1/text-to-speech/"
                + ELEVEN_VOICE_ID
            )

            eleven_headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }

            eleven_payload = {
                "text": reply,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.8,
                    "style": 0.15,
                    "use_speaker_boost": True,
                },
            }

            tts_response = requests.post(
                eleven_url,
                headers=eleven_headers,
                json=eleven_payload,
                timeout=60,
            )

            tts_response.raise_for_status()

            audio_base64 = base64.b64encode(
                tts_response.content
            ).decode("utf-8")

            st.session_state.audio_to_play = audio_base64

        st.session_state.processing = False

        st.rerun()

    except Exception as e:

        st.session_state.processing = False

        st.error(
            "J.A.R.V.I.S. ERROR: " + str(e)
        )
