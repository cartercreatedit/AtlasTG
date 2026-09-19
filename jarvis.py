import streamlit as st
from groq import Groq
import base64
import requests
import tempfile
import json
import streamlit.components.v1 as components

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered"
)

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]
ELEVEN_VOICE_ID = st.secrets.get(
    "ELEVEN_VOICE_ID",
    "bfGb7JTLUnZebZRiFYyq"
)

client = Groq(api_key=GROQ_API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a personal AI assistant. "
                "Address Carter as sir or Mr. Robinson when appropriate. "
                "Keep responses short, natural and conversational. "
                "Do not use markdown."
            )
        }
    ]

if "processing" not in st.session_state:
    st.session_state.processing = False


# =========================================================
# JARVIS UI
# =========================================================

jarvis_html = r"""
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
}

body {
    height: 330px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: Arial, sans-serif;
}

#main {
    display: flex;
    flex-direction: column;
    align-items: center;
}

#orb {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 2px solid #00f2fe;

    box-shadow:
        0 0 15px #00f2fe,
        0 0 35px rgba(0,242,254,.7),
        inset 0 0 25px rgba(0,242,254,.5);

    display: flex;
    justify-content: center;
    align-items: center;

    cursor: pointer;

    animation: pulse 3s infinite;
}

#orb.recording {
    animation: recording 1s infinite;
}

#orb.processing {
    animation: processing 1s infinite;
}

#inner {
    width: 105px;
    height: 105px;
    border-radius: 50%;

    border: 1px solid rgba(0,242,254,.65);

    box-shadow:
        inset 0 0 20px rgba(0,242,254,.35),
        0 0 15px rgba(0,242,254,.25);

    display: flex;
    justify-content: center;
    align-items: center;

    color: #00f2fe;
    font-size: 42px;

    text-shadow: 0 0 15px #00f2fe;
}

#name {
    margin-top: 20px;
    color: #00f2fe;
    font-size: 20px;
    letter-spacing: 5px;
    text-shadow: 0 0 10px rgba(0,242,254,.8);
}

#status {
    margin-top: 8px;
    color: rgba(0,242,254,.7);
    font-size: 11px;
    letter-spacing: 3px;
}

@keyframes pulse {
    0%,100% {
        box-shadow:
            0 0 15px #00f2fe,
            0 0 35px rgba(0,242,254,.7),
            inset 0 0 25px rgba(0,242,254,.5);
    }

    50% {
        box-shadow:
            0 0 20px #00f2fe,
            0 0 50px rgba(0,242,254,.8),
            inset 0 0 30px rgba(0,242,254,.6);
    }
}

@keyframes recording {
    0%,100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.06);
    }
}

@keyframes processing {
    0%,100% {
        transform: scale(.97);
    }

    50% {
        transform: scale(1.03);
    }
}
</style>
</head>

<body>

<div id="main">

    <div id="orb">
        <div id="inner">✦</div>
    </div>

    <div id="name">J.A.R.V.I.S.</div>

    <div id="status">VOICE CORE ONLINE</div>

</div>

<script>

const orb = document.getElementById("orb");
const status = document.getElementById("status");

let recorder = null;
let chunks = [];

let analyser = null;
let audioContext = null;

let silenceTimer = null;
let animationFrame = null;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;


function setStatus(value) {
    status.textContent = value;
}


function sendToStreamlit(base64) {

    const message = {
        type: "streamlit:setComponentValue",
        value: {
            audio: base64
        }
    };

    window.parent.postMessage(
        message,
        "*"
    );
}


function stopRecording() {

    if (!recorder) {
        return;
    }

    if (recorder.state !== "inactive") {
        recorder.stop();
    }

    if (silenceTimer) {
        clearTimeout(silenceTimer);
        silenceTimer = null;
    }

    if (animationFrame) {
        cancelAnimationFrame(animationFrame);
        animationFrame = null;
    }

    if (audioContext) {
        audioContext.close().catch(function(){});
        audioContext = null;
    }

    orb.classList.remove("recording");
    orb.classList.add("processing");

    setStatus("NEURAL RESPONSE");
}


function detectSilence() {

    if (!analyser || !recorder) {
        return;
    }

    const data =
        new Uint8Array(analyser.fftSize);

    analyser.getByteTimeDomainData(data);

    let total = 0;

    for (let i = 0; i < data.length; i++) {

        const difference =
            data[i] - 128;

        total +=
            difference * difference;
    }

    const rms =
        Math.sqrt(
            total / data.length
        );


    if (rms < SILENCE_THRESHOLD) {

        if (!silenceTimer) {

            silenceTimer =
                setTimeout(
                    stopRecording,
                    SILENCE_DURATION
                );
        }

    } else {

        if (silenceTimer) {

            clearTimeout(
                silenceTimer
            );

            silenceTimer = null;
        }
    }


    animationFrame =
        requestAnimationFrame(
            detectSilence
        );
}


async function startRecording() {

    if (
        recorder &&
        recorder.state === "recording"
    ) {
        return;
    }


    try {

        setStatus("LISTENING");


        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });


        chunks = [];


        recorder =
            new MediaRecorder(stream);


        recorder.ondataavailable =
            function(event) {

                if (event.data.size > 0) {

                    chunks.push(
                        event.data
                    );
                }
            };


        recorder.onstop =
            function() {

                stream
                    .getTracks()
                    .forEach(
                        function(track) {
                            track.stop();
                        }
                    );


                const blob =
                    new Blob(
                        chunks,
                        {
                            type: "audio/webm"
                        }
                    );


                const reader =
                    new FileReader();


                reader.onloadend =
                    function() {

                        const base64 =
                            reader.result
                                .split(",")[1];

                        sendToStreamlit(
                            base64
                        );
                    };


                reader.readAsDataURL(
                    blob
                );
            };


        audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();


        const source =
            audioContext.createMediaStreamSource(
                stream
            );


        analyser =
            audioContext.createAnalyser();


        analyser.fftSize = 2048;


        source.connect(
            analyser
        );


        recorder.start();


        orb.classList.add(
            "recording"
        );


        detectSilence();


    } catch (error) {

        console.error(error);

        setStatus(
            "MICROPHONE ERROR"
        );

        orb.classList.remove(
            "recording"
        );
    }
}


orb.addEventListener(
    "click",
    startRecording
);

</script>

</body>
</html>
"""


# =========================================================
# USE STREAMLIT'S BUILT-IN HTML COMPONENT
# =========================================================

jarvis_html_result = components.html(
    jarvis_html,
    height=330,
    scrolling=False
)


# =========================================================
# VOICE PROCESSING
# =========================================================

if (
    isinstance(jarvis_html_result, dict)
    and jarvis_html_result.get("audio")
    and not st.session_state.processing
):

    st.session_state.processing = True

    try:

        audio_base64 = jarvis_html_result["audio"]

        audio_bytes = base64.b64decode(
            audio_base64
        )


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_audio:

            temp_audio.write(
                audio_bytes
            )

            temp_audio_path = (
                temp_audio.name
            )


        with open(
            temp_audio_path,
            "rb"
        ) as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )


        try:
            os.remove(
                temp_audio_path
            )
        except Exception:
            pass


        user_text = str(
            transcription
        ).strip()


        if user_text:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": user_text
                }
            )


            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=300
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
                    "role": "assistant",
                    "content": reply
                }
            )


            # =============================================
            # ELEVENLABS
            # =============================================

            eleven_url = (
                "https://api.elevenlabs.io/v1/text-to-speech/"
                + ELEVEN_VOICE_ID
            )


            eleven_headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }


            eleven_payload = {
                "text": reply,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.8
                }
            }


            response = requests.post(
                eleven_url,
                headers=eleven_headers,
                json=eleven_payload,
                timeout=60
            )


            response.raise_for_status()


            audio_out = base64.b64encode(
                response.content
            ).decode("utf-8")


            safe_audio = json.dumps(
                audio_out
            )


            # =============================================
            # PLAY AUDIO
            # =============================================

            components.html(
                f"""
                <audio
                    autoplay
                    controls="false"
                    style="display:none;"
                >
                    <source
                        src="data:audio/mpeg;base64,{safe_audio}"
                        type="audio/mpeg"
                    >
                </audio>

                <script>
                    const audio =
                        document.querySelector("audio");

                    if (audio) {{
                        audio.play().catch(
                            function(error) {{
                                console.error(error);
                            }}
                        );
                    }}
                </script>
                """,
                height=1
            )


    except Exception as error:

        st.error(
            "J.A.R.V.I.S. ERROR: "
            + str(error)
        )


    finally:

        st.session_state.processing = False
