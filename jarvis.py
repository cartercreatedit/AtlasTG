import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile

st.set_page_config(page_title="J.A.R.V.I.S. Core", layout="centered")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]
ELEVEN_VOICE_ID = st.secrets.get("ELEVEN_VOICE_ID", "bfGb7JTLUnZebZRiFYyq")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a personal AI assistant. "
                "Address Carter as sir or Mr. Robinson when appropriate. "
                "Keep responses concise and natural for voice. "
                "Do not use markdown."
            )
        }
    ]

if "processing" not in st.session_state:
    st.session_state.processing = False

COMPONENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "jarvis_frontend"
)

os.makedirs(COMPONENT_DIR, exist_ok=True)

FRONTEND = r"""
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

#status {
    margin-top: 30px;
    color: #00f2fe;
    font-size: 13px;
    letter-spacing: 3px;
    opacity: .75;
    height: 18px;
}

#substatus {
    margin-top: 10px;
    color: #777;
    font-size: 11px;
    letter-spacing: 2px;
    height: 15px;
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
let sending = false;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;

const core = document.getElementById("core");
const statusEl = document.getElementById("status");
const substatusEl = document.getElementById("substatus");

function streamlitMessage(type, value) {
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

function setStatus(a, b, mode) {
    statusEl.textContent = a;
    substatusEl.textContent = b;

    document.body.classList.remove("listening");
    document.body.classList.remove("processing");

    if (mode) {
        document.body.classList.add(mode);
    }
}

function startListening() {

    if (listening || sending) {
        return;
    }

    navigator.mediaDevices.getUserMedia({
        audio: true
    }).then(function(stream) {

        listening = true;
        chunks = [];

        setStatus(
            "LISTENING",
            "SPEAK NOW",
            "listening"
        );

        recorder = new MediaRecorder(stream);

        recorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                chunks.push(event.data);
            }
        };

        recorder.onstop = function() {

            stream.getTracks().forEach(function(track) {
                track.stop();
            });

            if (audioContext) {
                try {
                    audioContext.close();
                } catch(e) {}

                audioContext = null;
            }

            if (chunks.length === 0) {
                listening = false;
                setStatus(
                    "J.A.R.V.I.S.",
                    "VOICE CORE ONLINE",
                    ""
                );
                return;
            }

            const blob = new Blob(chunks, {
                type: "audio/webm"
            });

            const reader = new FileReader();

            reader.onloadend = function() {

                const encoded = reader.result.split(",")[1];

                listening = false;
                sending = true;

                setStatus(
                    "PROCESSING",
                    "NEURAL RESPONSE",
                    "processing"
                );

                streamlitMessage(
                    "streamlit:setComponentValue",
                    encoded
                );
            };

            reader.readAsDataURL(blob);
        };

        recorder.start();

        try {

            audioContext = new AudioContext();

            const source =
                audioContext.createMediaStreamSource(stream);

            analyser = audioContext.createAnalyser();

            analyser.fftSize = 512;

            source.connect(analyser);

            monitor();

        } catch(e) {
            console.log(e);
        }

    }).catch(function() {

        setStatus(
            "MIC ERROR",
            "ALLOW MICROPHONE ACCESS",
            ""
        );
    });
}

function monitor() {

    if (!listening || !analyser) {
        return;
    }

    const data =
        new Uint8Array(analyser.frequencyBinCount);

    analyser.getByteFrequencyData(data);

    let total = 0;

    for (let i = 0; i < data.length; i++) {
        total += data[i];
    }

    const average = total / data.length;

    if (average < SILENCE_THRESHOLD) {

        if (!silenceTimer) {

            silenceTimer = setTimeout(function() {

                silenceTimer = null;

                if (
                    listening &&
                    recorder &&
                    recorder.state === "recording"
                ) {
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

    requestAnimationFrame(monitor);
}

function playAudio(base64) {

    sending = false;

    setStatus(
        "J.A.R.V.I.S.",
        "SPEAKING",
        ""
    );

    const audio = new Audio(
        "data:audio/mpeg;base64," + base64
    );

    audio.onended = function() {

        setStatus(
            "J.A.R.V.I.S.",
            "VOICE CORE ONLINE",
            ""
        );
    };

    audio.onerror = function() {

        setStatus(
            "J.A.R.V.I.S.",
            "VOICE CORE ONLINE",
            ""
        );
    };

    audio.play().catch(function() {

        setStatus(
            "J.A.R.V.I.S.",
            "VOICE CORE ONLINE",
            ""
        );
    });
}

core.addEventListener("click", function() {
    startListening();
});

window.addEventListener("message", function(event) {

    const data = event.data;

    if (!data) {
        return;
    }

    if (data.type === "streamlit:render") {

        const args = data.args || {};

        if (args.audio) {
            playAudio(args.audio);
        }

        if (args.reset) {

            sending = false;

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
});

</script>

</body>
</html>
"""

with open(
    os.path.join(COMPONENT_DIR, "index.html"),
    "w",
    encoding="utf-8"
) as f:
    f.write(FRONTEND)

jarvis = components.declare_component(
    "jarvis_voice_core",
    path=COMPONENT_DIR
)

# IMPORTANT:
# There is ONLY ONE component instance.
# Python sends the audio response back through the same component.

audio_input = jarvis(
    audio=None,
    reset=False,
    key="jarvis_voice_core"
)

if audio_input and not st.session_state.processing:

    st.session_state.processing = True

    try:

        audio_bytes = base64.b64decode(audio_input)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp:

            temp.write(audio_bytes)
            audio_path = temp.name

        with open(audio_path, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )

        user_text = str(transcription).strip()

        if user_text:

            st.session_state.messages.append({
                "role": "user",
                "content": user_text
            })

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=st.session_state.messages,
                temperature=0.3,
                max_tokens=200
            )

            reply = completion.choices[0].message.content.strip()

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply
            })

            response = requests.post(
                "https://api.elevenlabs.io/v1/text-to-speech/"
                + ELEVEN_VOICE_ID,
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

            if response.ok:

                audio_b64 = base64.b64encode(
                    response.content
                ).decode("utf-8")

                # Send the audio to the SAME component.
                jarvis(
                    audio=audio_b64,
                    reset=True,
                    key="jarvis_voice_core"
                )

            else:
                jarvis(
                    audio=None,
                    reset=True,
                    key="jarvis_voice_core"
                )

        else:

            jarvis(
                audio=None,
                reset=True,
                key="jarvis_voice_core"
            )

    except Exception as e:

        st.error("J.A.R.V.I.S. ERROR: " + str(e))

    finally:

        try:
            os.unlink(audio_path)
        except Exception:
            pass

        st.session_state.processing = False
