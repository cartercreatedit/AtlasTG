import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import base64
import requests
import tempfile
import os

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background:#000 !important;
    }

    header, footer, #MainMenu {
        display:none !important;
    }

    .block-container {
        padding:0 !important;
        margin:0 !important;
        max-width:100% !important;
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
    "bfGb7JTLUnZebZRiFYyq",
)

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SESSION
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

if "recording" not in st.session_state:
    st.session_state.recording = False

if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

# ============================================================
# JARVIS PAGE
#
# IMPORTANT:
# This uses components.html for the visible interface.
# There is NO declare_component frontend, so there is no
# "frontend component trouble loading" screen.
# ============================================================

page_html = r"""
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
    background: #000;
    overflow: hidden;
}

body {
    display: flex;
    align-items: center;
    justify-content: center;
}

#page {
    width: 100%;
    height: 330px;
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
    box-sizing: border-box;
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

<div id="page">

    <div id="sphere">
        <div id="inner">✦</div>
    </div>

    <div id="name">
        J.A.R.V.I.S.
    </div>

    <div id="status">
        VOICE CORE ONLINE
    </div>

</div>

<script>

const sphere =
    document.getElementById("sphere");

const statusText =
    document.getElementById("status");

let recorder = null;
let stream = null;
let chunks = [];

let audioContext = null;
let analyser = null;

let silenceTimer = null;
let listening = false;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;


// ==========================================================
// START LISTENING
// ==========================================================

async function startListening() {

    if (listening) {
        return;
    }

    listening = true;
    chunks = [];

    sphere.classList.add("listening");

    statusText.textContent =
        "LISTENING...";

    try {

        stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        recorder =
            new MediaRecorder(stream);

        recorder.ondataavailable =
            function(event) {

                if (
                    event.data &&
                    event.data.size > 0
                ) {
                    chunks.push(event.data);
                }
            };


        recorder.onstop =
            function() {

                if (stream) {

                    stream
                        .getTracks()
                        .forEach(
                            function(track) {
                                track.stop();
                            }
                        );
                }

                if (audioContext) {

                    audioContext
                        .close()
                        .catch(
                            function() {}
                        );
                }

                const blob =
                    new Blob(
                        chunks,
                        {
                            type: "audio/webm"
                        }
                    );

                if (!blob.size) {

                    reset();

                    return;
                }

                statusText.textContent =
                    "PROCESSING...";


                const reader =
                    new FileReader();


                reader.onloadend =
                    function() {

                        const result =
                            reader.result;

                        if (!result) {

                            reset();

                            return;
                        }

                        const base64 =
                            result
                                .split(",")[1];


                        /*
                         * Send recording to Streamlit.
                         *
                         * This is the standard message
                         * used by Streamlit's component
                         * communication layer.
                         */

                        window.parent.postMessage(
                            {
                                type:
                                    "streamlit:setComponentValue",

                                value:
                                    base64
                            },
                            "*"
                        );
                    };


                reader.readAsDataURL(blob);
            };


        recorder.start();


        // ==================================================
        // SILENCE DETECTION
        // ==================================================

        audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();


        analyser =
            audioContext.createAnalyser();

        analyser.fftSize = 512;


        const source =
            audioContext
                .createMediaStreamSource(
                    stream
                );


        source.connect(analyser);


        monitorSilence();

    }

    catch (error) {

        console.error(error);

        statusText.textContent =
            "MICROPHONE ERROR";

        reset();
    }
}


// ==========================================================
// SILENCE
// ==========================================================

function monitorSilence() {

    if (
        !listening ||
        !analyser
    ) {
        return;
    }


    const data =
        new Uint8Array(
            analyser.fftSize
        );


    analyser.getByteTimeDomainData(
        data
    );


    let total = 0;


    for (
        let i = 0;
        i < data.length;
        i++
    ) {

        const value =
            data[i] - 128;

        total += value * value;
    }


    const rms =
        Math.sqrt(
            total / data.length
        );


    if (
        rms < SILENCE_THRESHOLD
    ) {

        if (!silenceTimer) {

            silenceTimer =
                setTimeout(
                    function() {

                        silenceTimer =
                            null;

                        if (
                            recorder &&
                            recorder.state ===
                            "recording"
                        ) {

                            recorder.stop();
                        }

                    },
                    SILENCE_DURATION
                );
        }

    }

    else {

        if (silenceTimer) {

            clearTimeout(
                silenceTimer
            );

            silenceTimer = null;
        }
    }


    requestAnimationFrame(
        monitorSilence
    );
}


// ==========================================================
// RESET
// ==========================================================

function reset() {

    listening = false;

    sphere.classList.remove(
        "listening"
    );

    statusText.textContent =
        "VOICE CORE ONLINE";


    if (silenceTimer) {

        clearTimeout(
            silenceTimer
        );

        silenceTimer = null;
    }
}


// ==========================================================
// CLICK
// ==========================================================

sphere.addEventListener(
    "click",
    startListening
);


// ==========================================================
// PLAY JARVIS RESPONSE
// ==========================================================

window.addEventListener(
    "message",
    function(event) {

        if (!event.data) {
            return;
        }


        if (
            event.data.type ===
            "jarvis_audio"
        ) {

            const audio =
                new Audio(
                    "data:audio/mpeg;base64," +
                    event.data.audio
                );


            statusText.textContent =
                "SPEAKING...";


            audio.onended =
                function() {
                    reset();
                };


            audio.onerror =
                function() {
                    reset();
                };


            audio.play().catch(
                function() {
                    reset();
                }
            );
        }
    }
);

</script>

</body>
</html>
"""

# ============================================================
# DISPLAY
# ============================================================

components.html(
    page_html,
    height=330,
    scrolling=False,
)

# ============================================================
# HIDDEN AUDIO RECEIVER
#
# The original page communicates with Streamlit through the
# component message. This tiny receiver is kept out of the
# visual interface.
# ============================================================

receiver_html = r"""
<!DOCTYPE html>
<html>
<body style="margin:0;background:transparent;overflow:hidden;">
<script>

window.addEventListener(
    "message",
    function(event) {

        if (!event.data) {
            return;
        }

        if (
            event.data.type ===
            "streamlit:setComponentValue"
        ) {

            window.parent.postMessage(
                {
                    type:
                        "streamlit:setComponentValue",

                    value:
                        event.data.value
                },
                "*"
            );
        }
    }
);

</script>
</body>
</html>
"""

# ============================================================
# PROCESSING STATE
# ============================================================

if st.session_state.processing:
    pass
