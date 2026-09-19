import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile
import hashlib

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
ELEVEN_API_KEY = st.secrets.get("ELEVEN_API_KEY", os.getenv("ELEVEN_API_KEY"))
ELEVEN_VOICE_ID = st.secrets.get(
    "ELEVEN_VOICE_ID",
    os.getenv("ELEVEN_VOICE_ID", "bfGb7JTLUnZebZRiFYyq"),
)

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

if not ELEVEN_API_KEY:
    st.error("ELEVEN_API_KEY is missing.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a highly intelligent personal AI assistant. "
                "You are speaking to Carter Robinson, also known as Mr. Robinson or sir. "
                "Keep responses concise and natural because they will be spoken aloud. "
                "Do not use markdown, bullet points, or unnecessary formatting. "
                "Be helpful, calm, intelligent, and conversational."
            ),
        }
    ]

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None


component_dir = os.path.join(
    tempfile.gettempdir(),
    "jarvis_voice_component"
)

os.makedirs(component_dir, exist_ok=True)

component_html = r"""
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

.jarvis-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 300px;
}

.sphere-button {
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
    -webkit-tap-highlight-color: transparent;
    transition: transform .2s ease;
}

.sphere-button:hover {
    transform: scale(1.025);
}

.sphere-button:active {
    transform: scale(.98);
}

.inner-sphere {
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

.status {
    margin-top: 30px;
    color: #00f2fe;
    font-family: Arial,sans-serif;
    font-size: 13px;
    letter-spacing: 3px;
    opacity: .75;
}

.substatus {
    margin-top: 10px;
    color: #777;
    font-family: Arial,sans-serif;
    font-size: 11px;
    letter-spacing: 2px;
}

@keyframes pulse {
    0% {
        box-shadow:
            0 0 25px rgba(0,242,254,.35),
            0 0 70px rgba(0,242,254,.12),
            inset 0 0 30px rgba(0,242,254,.15);
    }

    50% {
        box-shadow:
            0 0 35px rgba(0,242,254,.5),
            0 0 90px rgba(0,242,254,.18),
            inset 0 0 35px rgba(0,242,254,.2);
    }

    100% {
        box-shadow:
            0 0 25px rgba(0,242,254,.35),
            0 0 70px rgba(0,242,254,.12),
            inset 0 0 30px rgba(0,242,254,.15);
    }
}

.listening {
    animation: listeningPulse .8s infinite alternate !important;
}

@keyframes listeningPulse {
    from {
        transform: scale(1);
    }

    to {
        transform: scale(1.05);
    }
}

.processing {
    animation: processingPulse 1s infinite alternate !important;
}

@keyframes processingPulse {
    from {
        transform: scale(1);
    }

    to {
        transform: scale(1.035);
    }
}
</style>
</head>

<body>

<div class="jarvis-container">

    <div id="sphere" class="sphere-button">

        <div class="inner-sphere">
            ✦
        </div>

    </div>

    <div id="status" class="status">
        J.A.R.V.I.S.
    </div>

    <div id="substatus" class="substatus">
        VOICE CORE ONLINE
    </div>

</div>

<script>

let mediaRecorder = null;
let audioChunks = [];
let audioContext = null;
let analyser = null;
let microphone = null;
let silenceTimer = null;
let animationFrame = null;
let isRecording = false;
let isProcessing = false;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;

const sphere = document.getElementById("sphere");
const status = document.getElementById("status");
const substatus = document.getElementById("substatus");


function setStatus(main, secondary) {
    status.textContent = main;
    substatus.textContent = secondary;
}


function sendValue(value) {
    window.parent.postMessage(
        {
            type: "streamlit:setComponentValue",
            value: value
        },
        "*"
    );
}


async function startListening() {

    if (isRecording || isProcessing) {
        return;
    }

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        audioChunks = [];

        mediaRecorder =
            new MediaRecorder(stream);

        mediaRecorder.ondataavailable =
            function(event) {

                if (
                    event.data &&
                    event.data.size > 0
                ) {
                    audioChunks.push(event.data);
                }

            };


        mediaRecorder.onstop =
            async function() {

                stream.getTracks().forEach(
                    track => track.stop()
                );

                if (audioContext) {
                    try {
                        await audioContext.close();
                    } catch (e) {}
                }

                cancelAnimationFrame(
                    animationFrame
                );

                clearTimeout(
                    silenceTimer
                );

                isRecording = false;
                isProcessing = true;

                sphere.classList.remove(
                    "listening"
                );

                sphere.classList.add(
                    "processing"
                );

                setStatus(
                    "PROCESSING",
                    "NEURAL RESPONSE"
                );

                const blob = new Blob(
                    audioChunks,
                    { type: "audio/webm" }
                );

                if (blob.size < 1000) {

                    isProcessing = false;

                    sphere.classList.remove(
                        "processing"
                    );

                    setStatus(
                        "J.A.R.V.I.S.",
                        "VOICE CORE ONLINE"
                    );

                    return;
                }

                const reader =
                    new FileReader();

                reader.onloadend =
                    function() {

                        const base64 =
                            reader.result.split(",")[1];

                        sendValue({
                            type: "audio",
                            audio: base64
                        });

                    };

                reader.readAsDataURL(blob);
            };


        mediaRecorder.start();

        isRecording = true;

        sphere.classList.add(
            "listening"
        );

        setStatus(
            "LISTENING",
            "SPEAK NOW"
        );


        audioContext = new (
            window.AudioContext ||
            window.webkitAudioContext
        )();

        analyser =
            audioContext.createAnalyser();

        analyser.fftSize = 2048;

        microphone =
            audioContext.createMediaStreamSource(
                stream
            );

        microphone.connect(analyser);

        monitorSilence();

    } catch (error) {

        isRecording = false;
        isProcessing = false;

        setStatus(
            "MICROPHONE ERROR",
            "ALLOW MICROPHONE ACCESS"
        );
    }
}


function monitorSilence() {

    if (!isRecording || !analyser) {
        return;
    }

    const data =
        new Uint8Array(
            analyser.fftSize
        );

    analyser.getByteTimeDomainData(data);

    let sum = 0;

    for (
        let i = 0;
        i < data.length;
        i++
    ) {

        const value =
            (data[i] - 128) / 128;

        sum += value * value;
    }

    const rms =
        Math.sqrt(
            sum / data.length
        );

    const volume =
        rms * 100;


    if (volume < SILENCE_THRESHOLD) {

        if (!silenceTimer) {

            silenceTimer =
                setTimeout(
                    stopListening,
                    SILENCE_DURATION
                );
        }

    } else {

        clearTimeout(
            silenceTimer
        );

        silenceTimer = null;
    }


    animationFrame =
        requestAnimationFrame(
            monitorSilence
        );
}


function stopListening() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {
        mediaRecorder.stop();
    }
}


sphere.addEventListener(
    "click",
    startListening
);


sphere.addEventListener(
    "touchend",
    function(event) {

        event.preventDefault();

        if (
            !isRecording &&
            !isProcessing
        ) {
            startListening();
        }

    },
    { passive: false }
);


/*
    Receive Streamlit render messages.
*/
window.addEventListener(
    "message",
    function(event) {

        const data = event.data;

        if (!data) {
            return;
        }


        if (
            data.type === "streamlit:render" &&
            data.args
        ) {

            const audio =
                data.args.audio;


            if (audio) {

                try {

                    const binary =
                        atob(audio);

                    const bytes =
                        new Uint8Array(
                            binary.length
                        );

                    for (
                        let i = 0;
                        i < binary.length;
                        i++
                    ) {
                        bytes[i] =
                            binary.charCodeAt(i);
                    }

                    const blob =
                        new Blob(
                            [bytes],
                            { type: "audio/mpeg" }
                        );

                    const url =
                        URL.createObjectURL(blob);

                    const audioElement =
                        new Audio(url);

                    audioElement.volume = 1;

                    audioElement.play()
                        .catch(() => {});


                    audioElement.onended =
                        function() {

                            URL.revokeObjectURL(
                                url
                            );

                            isProcessing = false;

                            sphere.classList.remove(
                                "processing"
                            );

                            setStatus(
                                "J.A.R.V.I.S.",
                                "VOICE CORE ONLINE"
                            );
                        };

                } catch (e) {

                    isProcessing = false;

                    sphere.classList.remove(
                        "processing"
                    );

                    setStatus(
                        "J.A.R.V.I.S.",
                        "VOICE CORE ONLINE"
                    );
                }
            }
        }
    }
);


/*
    Tell Streamlit the component is ready.
*/
window.parent.postMessage(
    {
        type: "streamlit:componentReady",
        apiVersion: 1
    },
    "*"
);


window.parent.postMessage(
    {
        type: "streamlit:setFrameHeight",
        height: 300
    },
    "*"
);

</script>

</body>
</html>
"""


component_path = os.path.join(
    component_dir,
    "index.html"
)

with open(
    component_path,
    "w",
    encoding="utf-8"
) as f:
    f.write(component_html)


jarvis_component = components.declare_component(
    "jarvis_voice_core",
    path=component_dir
)


def process_audio(audio_base64):

    try:

        audio_bytes =
            base64.b64decode(audio_base64)

        audio_hash = hashlib.sha256(
            audio_bytes
        ).hexdigest()

        if (
            st.session_state.last_audio_hash
            == audio_hash
        ):
            return

        st.session_state.last_audio_hash = (
            audio_hash
        )

        temp_audio_path = os.path.join(
            tempfile.gettempdir(),
            "jarvis_input.webm"
        )

        with open(
            temp_audio_path,
            "wb"
        ) as audio_file:
            audio_file.write(audio_bytes)


        with open(
            temp_audio_path,
            "rb"
        ) as audio_file:

            transcription =
                client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    response_format="text",
                )


        user_text = (
            transcription.text
            if hasattr(transcription, "text")
            else str(transcription)
        ).strip()


        if not user_text:
            return


        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text,
            }
        )


        completion =
            client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=st.session_state.messages,
                temperature=0.3,
                max_tokens=300,
                reasoning_effort="low",
            )


        reply =
            completion.choices[0].message.content.strip()


        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )


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


        eleven_response = requests.post(
            eleven_url,
            headers=eleven_headers,
            json=eleven_payload,
            timeout=60,
        )

        eleven_response.raise_for_status()


        st.session_state.audio_to_play =
            base64.b64encode(
                eleven_response.content
            ).decode("utf-8")


    except Exception as e:

        st.session_state.audio_to_play = None

        st.error(
            "J.A.R.V.I.S. ERROR: "
            + str(e)
        )


audio_result = jarvis_component(
    audio=None,
    key="jarvis_voice",
    default=None,
)


if (
    isinstance(audio_result, dict)
    and audio_result.get("type") == "audio"
):

    audio_data =
        audio_result.get("audio")

    if audio_data:
        process_audio(audio_data)


audio_for_component =
    st.session_state.audio_to_play

st.session_state.audio_to_play = None


# ONLY ONE SPHERE
jarvis_component(
    audio=audio_for_component,
    key="jarvis_voice",
    default=None,
)


st.markdown(
    """
    <style>

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .stApp {
        background: #000;
    }

    [data-testid="stAppViewContainer"] {
        background: #000;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    </style>
    """,
    unsafe_allow_html=True,
)
