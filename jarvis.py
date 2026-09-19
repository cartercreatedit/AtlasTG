import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import base64
import requests
import tempfile
import os


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
                "Keep responses short and natural. "
                "Do not use markdown."
            )
        }
    ]


if "processing" not in st.session_state:
    st.session_state.processing = False


# =========================================================
# J.A.R.V.I.S. FRONTEND
# =========================================================

component_dir = os.path.join(
    tempfile.gettempdir(),
    "jarvis_frontend"
)

os.makedirs(component_dir, exist_ok=True)


html = r"""
<!DOCTYPE html>
<html>
<head>

<style>

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: transparent;
    overflow: hidden;
}

#app {
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

.processing {
    animation: pulse 1s infinite ease-in-out !important;
}

</style>

</head>

<body>

<div id="app">

    <div id="orb">

        <div id="inner">
            ✦
        </div>

    </div>

    <div id="name">
        J.A.R.V.I.S.
    </div>

    <div id="status">
        VOICE CORE ONLINE
    </div>

</div>


<script>

function sendMessage(type, data) {

    window.parent.postMessage(
        Object.assign(
            {
                isStreamlitMessage: true,
                type: type
            },
            data || {}
        ),
        "*"
    );

}


function setReady() {

    sendMessage(
        "streamlit:componentReady",
        {
            apiVersion: 1
        }
    );

    sendMessage(
        "streamlit:setFrameHeight",
        {
            height: 330
        }
    );

}


const orb = document.getElementById("orb");
const status = document.getElementById("status");

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
    status.textContent = text;
}


async function startRecording() {

    if (recording) {
        return;
    }

    try {

        setStatus("INITIALIZING MICROPHONE");

        stream =
            await navigator.mediaDevices.getUserMedia({
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

                const result = reader.result;

                if (!result) {
                    setStatus("VOICE CORE ONLINE");
                    return;
                }

                const base64 =
                    result.split(",")[1];

                sendMessage(
                    "streamlit:setComponentValue",
                    {
                        value: {
                            audio: base64
                        }
                    }
                );

            };

            reader.readAsDataURL(blob);

        };


        audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

        analyser =
            audioContext.createAnalyser();

        analyser.fftSize = 2048;

        analyser.smoothingTimeConstant = 0.8;

        microphone =
            audioContext.createMediaStreamSource(
                stream
            );

        microphone.connect(analyser);

        recorder.start();

        recording = true;

        silenceStart = null;

        orb.classList.add("recording");

        setStatus("LISTENING");

        checkSilence();

    }

    catch (error) {

        console.error(error);

        setStatus("MICROPHONE ACCESS REQUIRED");

        cleanup();

    }

}


function checkSilence() {

    if (!recording || !analyser) {
        return;
    }

    const data =
        new Uint8Array(analyser.fftSize);

    analyser.getByteTimeDomainData(data);

    let sum = 0;

    for (
        let i = 0;
        i < data.length;
        i++
    ) {

        const value = data[i] - 128;

        sum += value * value;

    }

    const rms =
        Math.sqrt(sum / data.length);


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
        checkSilence
    );

}


function stopRecording() {

    if (!recording) {
        return;
    }

    recording = false;

    orb.classList.remove("recording");
    orb.classList.add("processing");

    setStatus(
        "PROCESSING NEURAL RESPONSE"
    );

    if (
        recorder &&
        recorder.state !== "inactive"
    ) {

        recorder.stop();

    }

    cleanup();

}


function cleanup() {

    if (stream) {

        stream.getTracks().forEach(
            function(track) {
                track.stop();
            }
        );

        stream = null;

    }

    if (audioContext) {

        try {
            audioContext.close();
        }

        catch (error) {}

        audioContext = null;

    }

    analyser = null;
    microphone = null;

}


orb.addEventListener(
    "click",
    function() {

        if (!recording) {
            startRecording();
        }

    }
);


window.addEventListener(
    "message",
    function(event) {

        if (!event.data) {
            return;
        }

        if (
            event.data.type ===
            "jarvis:play"
        ) {

            const audio =
                new Audio(
                    "data:audio/mpeg;base64," +
                    event.data.audio
                );

            setStatus("SPEAKING");

            audio.play().catch(
                function(error) {
                    console.error(error);
                }
            );

            audio.onended = function() {

                orb.classList.remove(
                    "processing"
                );

                setStatus(
                    "VOICE CORE ONLINE"
                );

            };

        }

    }
);


window.addEventListener(
    "load",
    function() {
        setReady();
    }
);


setReady();

</script>

</body>
</html>
"""


component_file = os.path.join(
    component_dir,
    "index.html"
)

with open(
    component_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(html)


# =========================================================
# COMPONENT
# =========================================================

jarvis_component = components.declare_component(
    "jarvis_voice_core",
    path=component_dir
)


audio_data = jarvis_component(
    key="jarvis_voice",
    default=None
)


# =========================================================
# PROCESS AUDIO
# =========================================================

if (
    isinstance(audio_data, dict)
    and audio_data.get("audio")
    and not st.session_state.processing
):

    st.session_state.processing = True

    try:

        audio_bytes = base64.b64decode(
            audio_data["audio"]
        )

        audio_path = os.path.join(
            tempfile.gettempdir(),
            "jarvis_audio.webm"
        )

        with open(
            audio_path,
            "wb"
        ) as file:

            file.write(audio_bytes)


        # =================================================
        # TRANSCRIPTION
        # =================================================

        with open(
            audio_path,
            "rb"
        ) as audio_file:

            transcription = (
                client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    response_format="text"
                )
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
                ""
            ).strip()


        try:
            os.remove(audio_path)
        except OSError:
            pass


        if not user_text:
            st.session_state.processing = False
            st.rerun()


        # =================================================
        # GROQ
        # =================================================

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )


        completion = (
            client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=st.session_state.messages,
                temperature=0.3,
                max_tokens=200
            )
        )


        reply = (
            completion.choices[0]
            .message.content
            .strip()
        )


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


        response_audio = base64.b64encode(
            response.content
        ).decode("utf-8")


        # =================================================
        # SEND AUDIO TO JARVIS FRONTEND
        # =================================================

        components.html(
            f"""
            <script>

            window.parent.postMessage(
                {{
                    type: "jarvis:play",
                    audio: {response_audio!r}
                }},
                "*"
            );

            </script>
            """,
            height=1
        )


    except Exception as error:

        st.error(
            f"J.A.R.V.I.S. ERROR: {error}"
        )


    finally:

        st.session_state.processing = False
