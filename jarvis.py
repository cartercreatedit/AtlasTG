import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
        padding-top:0;
        padding-bottom:0;
        max-width:100%;
    }

    iframe {
        border:none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# API
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
# MEMORY
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
# COMPONENT
# ============================================================

COMPONENT_DIR = os.path.join(
    tempfile.gettempdir(),
    "jarvis_core_component"
)

os.makedirs(COMPONENT_DIR, exist_ok=True)

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
html,body {
    margin:0;
    padding:0;
    width:100%;
    height:100%;
    background:transparent;
    overflow:hidden;
}

body {
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}

#sphere {
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
    cursor:pointer;
    box-sizing:border-box;
}

#inner {
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
}

#name {
    margin-top:30px;
    color:#00f2fe;
    font-family:Arial,sans-serif;
    font-size:13px;
    letter-spacing:3px;
    opacity:.75;
}

#status {
    margin-top:10px;
    color:#777;
    font-family:Arial,sans-serif;
    font-size:11px;
    letter-spacing:2px;
}

@keyframes pulse {
    0%,100% {
        transform:scale(1);
        opacity:.88;
    }

    50% {
        transform:scale(1.035);
        opacity:1;
    }
}

.listening {
    animation:listeningPulse .8s infinite ease-in-out !important;
}

@keyframes listeningPulse {
    0%,100% {
        transform:scale(1);
        box-shadow:
            0 0 25px rgba(0,242,254,.35),
            0 0 70px rgba(0,242,254,.12),
            inset 0 0 30px rgba(0,242,254,.15);
    }

    50% {
        transform:scale(1.07);
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
const sphere = document.getElementById("sphere");
const statusText = document.getElementById("status");

let recorder = null;
let chunks = [];
let analyser = null;
let audioContext = null;
let stream = null;
let silenceTimeout = null;
let listening = false;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;

function ready() {
    window.parent.postMessage(
        {
            type:"streamlit:componentReady",
            apiVersion:1
        },
        "*"
    );

    window.parent.postMessage(
        {
            type:"streamlit:setFrameHeight",
            height:330
        },
        "*"
    );
}

function sendAudio(base64) {
    window.parent.postMessage(
        {
            type:"streamlit:setComponentValue",
            value:base64
        },
        "*"
    );
}

function reset() {
    listening = false;
    sphere.classList.remove("listening");
    statusText.textContent = "VOICE CORE ONLINE";

    if (silenceTimeout) {
        clearTimeout(silenceTimeout);
        silenceTimeout = null;
    }
}

async function startListening() {

    if (listening) {
        return;
    }

    listening = true;
    chunks = [];

    sphere.classList.add("listening");
    statusText.textContent = "LISTENING...";

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            audio:true
        });

        recorder = new MediaRecorder(stream);

        recorder.ondataavailable = function(event) {
            if (event.data && event.data.size > 0) {
                chunks.push(event.data);
            }
        };

        recorder.onstop = function() {

            if (stream) {
                stream.getTracks().forEach(function(track) {
                    track.stop();
                });
            }

            if (audioContext) {
                audioContext.close().catch(function(){});
            }

            const blob = new Blob(
                chunks,
                {type:"audio/webm"}
            );

            if (!blob.size) {
                reset();
                return;
            }

            statusText.textContent = "PROCESSING...";

            const reader = new FileReader();

            reader.onloadend = function() {

                const result = reader.result;

                if (!result) {
                    reset();
                    return;
                }

                const base64 = result.split(",")[1];

                sendAudio(base64);
            };

            reader.readAsDataURL(blob);
        };

        recorder.start();

        audioContext = new (
            window.AudioContext ||
            window.webkitAudioContext
        )();

        analyser = audioContext.createAnalyser();

        analyser.fftSize = 512;

        const source =
            audioContext.createMediaStreamSource(stream);

        source.connect(analyser);

        monitor();

    } catch (error) {

        console.error(error);

        statusText.textContent = "MICROPHONE ERROR";

        reset();
    }
}

function monitor() {

    if (!listening || !analyser) {
        return;
    }

    const data = new Uint8Array(
        analyser.fftSize
    );

    analyser.getByteTimeDomainData(data);

    let sum = 0;

    for (let i = 0; i < data.length; i++) {
        const value = data[i] - 128;
        sum += value * value;
    }

    const rms = Math.sqrt(
        sum / data.length
    );

    if (rms < SILENCE_THRESHOLD) {

        if (!silenceTimeout) {

            silenceTimeout = setTimeout(function() {

                silenceTimeout = null;

                if (
                    recorder &&
                    recorder.state === "recording"
                ) {
                    recorder.stop();
                }

            }, SILENCE_DURATION);
        }

    } else {

        if (silenceTimeout) {
            clearTimeout(silenceTimeout);
            silenceTimeout = null;
        }
    }

    requestAnimationFrame(monitor);
}

sphere.addEventListener(
    "click",
    startListening
);

window.addEventListener(
    "message",
    function(event) {

        if (!event.data) {
            return;
        }

        if (
            event.data.type ===
            "jarvis:play_audio"
        ) {

            const audio = new Audio(
                "data:audio/mpeg;base64," +
                event.data.audio
            );

            statusText.textContent =
                "SPEAKING...";

            audio.onended = function() {
                reset();
            };

            audio.onerror = function() {
                reset();
            };

            audio.play().catch(function() {
                reset();
            });
        }
    }
);

ready();
</script>

</body>
</html>
"""

component_file = os.path.join(
    COMPONENT_DIR,
    "index.html"
)

with open(
    component_file,
    "w",
    encoding="utf-8"
) as file:
    file.write(HTML)

jarvis_component = components.declare_component(
    "jarvis_core",
    path=COMPONENT_DIR
)

# ============================================================
# SINGLE COMPONENT — NO DUPLICATE BAR
# ============================================================

audio_to_play = st.session_state.audio_to_play
st.session_state.audio_to_play = None

audio_result = jarvis_component(
    audio=audio_to_play,
    key="jarvis_core_main",
    default=None,
)

# ============================================================
# PROCESS RECORDING
# ============================================================

if (
    audio_result
    and not st.session_state.processing
):

    st.session_state.processing = True

    try:

        audio_bytes = base64.b64decode(
            audio_result
        )

        audio_path = os.path.join(
            tempfile.gettempdir(),
            "jarvis_recording.webm"
        )

        with open(
            audio_path,
            "wb"
        ) as audio_file:
            audio_file.write(audio_bytes)

        # ----------------------------
        # TRANSCRIPTION
        # ----------------------------

        with open(
            audio_path,
            "rb"
        ) as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )

        user_text = str(
            transcription
        ).strip()

        if not user_text:
            st.session_state.processing = False
            st.rerun()

        # ----------------------------
        # CHAT
        # ----------------------------

        st.session_state.messages.append(
            {
                "role":"user",
                "content":user_text
            }
        )

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=st.session_state.messages,
            temperature=0.3,
            max_tokens=200
        )

        reply = (
            completion
            .choices[0]
            .message
            .content
            .strip()
        )

        st.session_state.messages.append(
            {
                "role":"assistant",
                "content":reply
            }
        )

        # ----------------------------
        # ELEVENLABS
        # ----------------------------

        if ELEVEN_API_KEY:

            eleven_url = (
                "https://api.elevenlabs.io/v1/text-to-speech/"
                + ELEVEN_VOICE_ID
            )

            response = requests.post(
                eleven_url,
                headers={
                    "xi-api-key":ELEVEN_API_KEY,
                    "Content-Type":"application/json",
                    "Accept":"audio/mpeg"
                },
                json={
                    "text":reply,
                    "model_id":"eleven_multilingual_v2",
                    "voice_settings":{
                        "stability":0.45,
                        "similarity_boost":0.8,
                        "style":0.15,
                        "use_speaker_boost":True
                    }
                },
                timeout=60
            )

            response.raise_for_status()

            st.session_state.audio_to_play = (
                base64.b64encode(
                    response.content
                ).decode("utf-8")
            )

        st.session_state.processing = False

        st.rerun()

    except Exception as error:

        st.session_state.processing = False

        st.error(
            "J.A.R.V.I.S. ERROR: "
            + str(error)
        )
