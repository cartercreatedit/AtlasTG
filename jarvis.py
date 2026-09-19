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
    layout="centered"
)


# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]

ELEVEN_VOICE_ID = st.secrets.get(
    "ELEVEN_VOICE_ID",
    "bfGb7JTLUnZebZRiFYyq"
)

client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# SESSION STATE
# =========================================================

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

if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

if "processing" not in st.session_state:
    st.session_state.processing = False


# =========================================================
# JARVIS FRONTEND
# =========================================================

jarvis_html = """
<!DOCTYPE html>

<html>

<head>

<style>

html, body {
    margin: 0;
    padding: 0;
    background: transparent;
    overflow: hidden;
}

#container {
    width: 100%;
    height: 330px;

    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

#orb {
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

#title {
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

    0% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.035);
    }

    100% {
        transform: scale(1);
    }

}

.recording {

    box-shadow:
        0 0 35px rgba(0,242,254,.6),
        0 0 90px rgba(0,242,254,.25),
        inset 0 0 35px rgba(0,242,254,.2) !important;

}

</style>

</head>

<body>

<div id="container">

    <div id="orb">

        <div id="inner">
            ✦
        </div>

    </div>

    <div id="title">
        J.A.R.V.I.S.
    </div>

    <div id="status">
        VOICE CORE ONLINE
    </div>

</div>


<script>

const orb = document.getElementById("orb");
const statusText = document.getElementById("status");

let recorder = null;
let chunks = [];
let stream = null;

let audioContext = null;
let analyser = null;
let microphone = null;

let recording = false;
let silenceStart = null;

const SILENCE_THRESHOLD = 8;
const SILENCE_DURATION = 1500;


function setStatus(text) {
    statusText.textContent = text;
}


async function startRecording() {

    if (recording) {
        return;
    }

    try {

        setStatus("INITIALIZING MICROPHONE");

        stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        chunks = [];

        recorder = new MediaRecorder(stream);

        recorder.ondataavailable = function(event) {

            if (event.data.size > 0) {
                chunks.push(event.data);
            }

        };


        recorder.onstop = function() {

            const blob = new Blob(
                chunks,
                {
                    type: recorder.mimeType || "audio/webm"
                }
            );

            const reader = new FileReader();

            reader.onloadend = function() {

                const base64 = reader.result.split(",")[1];

                window.parent.postMessage(
                    {
                        type: "streamlit:setComponentValue",
                        value: base64
                    },
                    "*"
                );

            };

            reader.readAsDataURL(blob);

        };


        audioContext = new (
            window.AudioContext ||
            window.webkitAudioContext
        )();

        microphone = audioContext.createMediaStreamSource(stream);

        analyser = audioContext.createAnalyser();

        analyser.fftSize = 2048;

        microphone.connect(analyser);

        recorder.start();

        recording = true;

        silenceStart = null;

        orb.classList.add("recording");

        setStatus("LISTENING");

        monitorSilence();

    }

    catch (error) {

        console.error(error);

        setStatus("MICROPHONE ACCESS REQUIRED");

    }

}


function monitorSilence() {

    if (!recording) {
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

        if (silenceStart === null) {
            silenceStart = Date.now();
        }

        if (
            Date.now() - silenceStart >=
            SILENCE_DURATION
        ) {

            stopRecording();

            return;

        }

    }

    else {

        silenceStart = null;

    }


    requestAnimationFrame(
        monitorSilence
    );

}


function stopRecording() {

    if (!recording) {
        return;
    }

    recording = false;

    orb.classList.remove("recording");

    setStatus("PROCESSING NEURAL RESPONSE");

    if (
        recorder &&
        recorder.state !== "inactive"
    ) {

        recorder.stop();

    }


    if (stream) {

        stream.getTracks().forEach(
            function(track) {
                track.stop();
            }
        );

    }


    if (audioContext) {

        audioContext.close();

    }

}


orb.addEventListener(
    "click",
    function() {

        if (recording) {

            stopRecording();

        }

        else {

            startRecording();

        }

    }
);


window.addEventListener(
    "message",
    function(event) {

        if (
            event.data &&
            event.data.type ===
            "jarvis:playAudio"
        ) {

            try {

                const audio = new Audio(
                    "data:audio/mpeg;base64," +
                    event.data.audio
                );

                audio.play();

                setStatus(
                    "VOICE CORE ONLINE"
                );

            }

            catch (error) {

                console.error(error);

            }

        }

    }
);

</script>

</body>

</html>
"""


# =========================================================
# COMPONENT
# =========================================================

jarvis_component = components.declare_component(
    "jarvis_voice_core",
    html=jarvis_html
)


# =========================================================
# DISPLAY COMPONENT
# =========================================================

audio_data = jarvis_component(
    key="jarvis_voice",
    default=None
)


# =========================================================
# PROCESS AUDIO
# =========================================================

if audio_data and not st.session_state.processing:

    st.session_state.processing = True

    try:

        if isinstance(audio_data, str):

            audio_base64 = audio_data

        elif isinstance(audio_data, dict):

            audio_base64 = audio_data.get(
                "base64",
                ""
            )

        else:

            audio_base64 = ""

        if not audio_base64:
            raise ValueError("No audio received.")

        audio_bytes = base64.b64decode(
            audio_base64
        )

        temp_audio_path = os.path.join(
            tempfile.gettempdir(),
            "jarvis_temp.webm"
        )


        with open(
            temp_audio_path,
            "wb"
        ) as audio_file:

            audio_file.write(
                audio_bytes
            )


        # =================================================
        # TRANSCRIPTION
        # =================================================

        with open(
            temp_audio_path,
            "rb"
        ) as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )


        if isinstance(
            transcription,
            str
        ):

            user_text = transcription.strip()

        else:

            user_text = getattr(
                transcription,
                "text",
                str(transcription)
            ).strip()


        try:

            os.remove(
                temp_audio_path
            )

        except OSError:

            pass


        if not user_text:

            st.session_state.processing = False

            st.rerun()


        # =================================================
        # CHAT
        # =================================================

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )


        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=st.session_state.messages,
            temperature=0.3,
            max_tokens=200
        )


        reply = completion.choices[
            0
        ].message.content.strip()


        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply
            }
        )


        # =================================================
        # ELEVENLABS
        # =================================================

        eleven_url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            + ELEVEN_VOICE_ID
        )


        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }


        payload = {
            "text": reply,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.8
            }
        }


        response = requests.post(
            eleven_url,
            headers=headers,
            json=payload,
            timeout=60
        )


        response.raise_for_status()


        audio_base64 = base64.b64encode(
            response.content
        ).decode("utf-8")


        # =================================================
        # PLAY AUDIO
        # =================================================

        components.html(
            f"""
            <script>

            const audio =
                new Audio(
                    "data:audio/mpeg;base64,{audio_base64}"
                );

            audio.play().catch(
                function(error) {{
                    console.log(error);
                }}
            );

            </script>
            """,
            height=0
        )


    except Exception as error:

        st.error(
            f"J.A.R.V.I.S. ERROR: {error}"
        )


    finally:

        st.session_state.processing = False
