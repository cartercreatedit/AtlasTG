import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile
import shutil

st.set_page_config(page_title="J.A.R.V.I.S. Core", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]
ELEVEN_VOICE_ID = st.secrets.get("ELEVEN_VOICE_ID", "bfGb7JTLUnZebZRiFYyq")

client = Groq(api_key=GROQ_API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a personal AI assistant. "
                "Address Carter as sir or Mr. Robinson when appropriate. "
                "Keep responses concise and natural for voice. "
                "Do not use markdown."
            ),
        }
    ]

# ---------------------------------------------------------
# FRONTEND COMPONENT
# ---------------------------------------------------------

COMPONENT_DIR = os.path.join(
    tempfile.gettempdir(),
    "jarvis_frontend_final"
)

os.makedirs(COMPONENT_DIR, exist_ok=True)

index_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
html, body {
    margin: 0;
    padding: 0;
    background: transparent;
    overflow: hidden;
    width: 100%;
    height: 100%;
}

body {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    font-family: Arial, sans-serif;
}

#core {
    margin-top: 10px;
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
    transition: all .25s ease;
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
    transition: all .25s ease;
}

#status {
    margin-top: 30px;
    color: #00f2fe;
    font-size: 13px;
    letter-spacing: 3px;
    opacity: .75;
    height: 18px;
    text-align: center;
}

#substatus {
    margin-top: 10px;
    color: #777;
    font-size: 11px;
    letter-spacing: 2px;
    height: 15px;
    text-align: center;
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        opacity: .9;
    }
    50% {
        transform: scale(1.035);
        opacity: 1;
    }
}

.listening #core {
    box-shadow:
        0 0 35px rgba(0,242,254,.7),
        0 0 100px rgba(0,242,254,.3),
        inset 0 0 40px rgba(0,242,254,.25);
    transform: scale(1.04);
}

.listening #inner {
    box-shadow:
        0 0 40px rgba(0,242,254,.7),
        inset 0 0 35px rgba(0,242,254,.2);
}

.processing #core {
    animation: pulse .8s infinite ease-in-out;
}

</style>
</head>

<body>

<div id="core">
    <div id="inner">✦</div>
</div>

<div id="status">J.A.R.V.I.S.</div>
<div id="substatus">VOICE CORE ONLINE</div>

<script>
let recorder = null;
let chunks = [];
let silenceTimer = null;
let analyser = null;
let audioContext = null;
let listening = false;
let processing = false;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;

const core = document.getElementById("core");
const statusText = document.getElementById("status");
const substatusText = document.getElementById("substatus");

function sendMessage(type, value) {
    window.parent.postMessage({
        isStreamlitMessage: true,
        type: type,
        value: value
    }, "*");
}

function setHeight() {
    window.parent.postMessage({
        isStreamlitMessage: true,
        type: "streamlit:setFrameHeight",
        height: 260
    }, "*");
}

function setValue(value) {
    sendMessage("streamlit:setComponentValue", value);
}

function setStatus(main, sub, className) {
    statusText.textContent = main;
    substatusText.textContent = sub;

    document.body.classList.remove("listening");
    document.body.classList.remove("processing");

    if (className) {
        document.body.classList.add(className);
    }
}

async function startListening() {
    if (listening || processing) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        listening = true;
        chunks = [];

        setStatus("LISTENING", "SPEAK NOW", "listening");

        recorder = new MediaRecorder(stream);

        recorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                chunks.push(event.data);
            }
        };

        recorder.onstop = function() {
            stream.getTracks().forEach(track => track.stop());

            if (audioContext) {
                try {
                    audioContext.close();
                } catch(e) {}
                audioContext = null;
            }

            if (chunks.length === 0) {
                listening = false;
                setStatus("J.A.R.V.I.S.", "VOICE CORE ONLINE", "");
                return;
            }

            const blob = new Blob(chunks, {
                type: "audio/webm"
            });

            const reader = new FileReader();

            reader.onloadend = function() {
                const base64 = reader.result.split(",")[1];

                listening = false;
                processing = true;

                setStatus(
                    "PROCESSING",
                    "NEURAL RESPONSE",
                    "processing"
                );

                setValue(base64);
            };

            reader.readAsDataURL(blob);
        };

        recorder.start();

        try {
            audioContext = new AudioContext();

            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();

            analyser.fftSize = 512;

            source.connect(analyser);

            monitorSilence();

        } catch(e) {
            console.log("Audio analyser unavailable:", e);
        }

    } catch(error) {
        listening = false;
        processing = false;

        setStatus(
            "MIC ERROR",
            "ALLOW MICROPHONE ACCESS",
            ""
        );
    }
}

function monitorSilence() {
    if (!listening || !analyser) return;

    const data = new Uint8Array(analyser.frequencyBinCount);

    analyser.getByteFrequencyData(data);

    let sum = 0;

    for (let i = 0; i < data.length; i++) {
        sum += data[i];
    }

    const average = sum / data.length;

    if (average < SILENCE_THRESHOLD) {

        if (!silenceTimer) {
            silenceTimer = setTimeout(() => {

                silenceTimer = null;

                if (listening && recorder && recorder.state === "recording") {
                    recorder.stop();
                }

            }, SILENCE_DURATION);
        }

    } else {

        if (silenceTimer) {
            clearTimeout(silenceTimer);
            silenceTimer = null;
        }
    }

    requestAnimationFrame(monitorSilence);
}

async function playAudio(base64Audio) {
    try {
        processing = false;

        setStatus(
            "J.A.R.V.I.S.",
            "SPEAKING",
            ""
        );

        const audio = new Audio(
            "data:audio/mpeg;base64," + base64Audio
        );

        audio.onended = function() {
            setStatus(
                "J.A.R.V.I.S.",
                "VOICE CORE ONLINE",
                ""
            );
        };

        await audio.play();

    } catch(error) {
        processing = false;

        setStatus(
            "J.A.R.V.I.S.",
            "VOICE CORE ONLINE",
            ""
        );
    }
}

core.addEventListener("click", function() {
    startListening();
});

window.addEventListener("message", function(event) {

    const data = event.data;

    if (!data) return;

    if (data.type === "streamlit:render") {

        const args = data.args || {};

        if (args.audio) {
            playAudio(args.audio);
        }

        if (args.reset === true) {
            processing = false;

            setStatus(
                "J.A.R.V.I.S.",
                "VOICE CORE ONLINE",
                ""
            );
        }
    }
});

window.addEventListener("load", function() {

    window.parent.postMessage({
        isStreamlitMessage: true,
        type: "streamlit:componentReady",
        apiVersion: 1
    }, "*");

    setHeight();

    setTimeout(setHeight, 100);
});

</script>

</body>
</html>
"""

index_path = os.path.join(COMPONENT_DIR, "index.html")

try:
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
except Exception:
    pass

jarvis_component = components.declare_component(
    "jarvis_frontend_final",
    path=COMPONENT_DIR
)

# ---------------------------------------------------------
# BACKEND
# ---------------------------------------------------------

if "audio_to_process" not in st.session_state:
    st.session_state.audio_to_process = None

audio_bytes = jarvis_component(
    audio=None,
    reset=False,
    default=None,
    key="jarvis_main_component"
)

if audio_bytes:
    st.session_state.audio_to_process = audio_bytes

# ---------------------------------------------------------
# PROCESS AUDIO
# ---------------------------------------------------------

if st.session_state.audio_to_process:

    encoded_audio = st.session_state.audio_to_process
    st.session_state.audio_to_process = None

    try:
        audio_data = base64.b64decode(encoded_audio)

        temp_audio = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        )

        temp_audio.write(audio_data)
        temp_audio.close()

        with open(temp_audio.name, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )

        user_text = str(transcription).strip()

        if not user_text:
            st.rerun()

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=st.session_state.messages,
            temperature=0.3,
            max_tokens=200
        )

        reply = completion.choices[0].message.content.strip()

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        # ElevenLabs TTS
        tts_url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            + ELEVEN_VOICE_ID
        )

        tts_response = requests.post(
            tts_url,
            headers={
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            },
            json={
                "text": reply,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.8
                }
            },
            timeout=60
        )

        if tts_response.ok:

            audio_b64 = base64.b64encode(
                tts_response.content
            ).decode("utf-8")

            jarvis_component(
                audio=audio_b64,
                reset=True,
                default=None,
                key="jarvis_audio_component"
            )

        else:

            jarvis_component(
                audio=None,
                reset=True,
                default=None,
                key="jarvis_reset_component"
            )

    except Exception as e:

        st.error(
            "J.A.R.V.I.S. ERROR: " + str(e)
        )

    finally:

        try:
            os.unlink(temp_audio.name)
        except Exception:
            pass
