import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile
import uuid

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
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

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a personal AI assistant for Carter "
                "Robinson. Address him naturally as sir when appropriate. "
                "Keep spoken answers concise and natural. Do not use markdown "
                "unless absolutely necessary."
            ),
        }
    ]

if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

if "processing" not in st.session_state:
    st.session_state.processing = False

if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None

if "pending_play_id" not in st.session_state:
    st.session_state.pending_play_id = None

if "pending_state" not in st.session_state:
    st.session_state.pending_state = "ready"


# =========================================================
# FRONTEND FOLDER
# =========================================================

COMPONENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "jarvis_frontend",
)

os.makedirs(COMPONENT_DIR, exist_ok=True)


# =========================================================
# FRONTEND
# =========================================================

HTML = r"""
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
    align-items: center;
    justify-content: center;
}

#container {
    width: 100%;
    height: 100%;
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
    user-select: none;
    -webkit-tap-highlight-color: transparent;
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
    min-height: 14px;
}

@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: .9;
    }

    50% {
        transform: scale(1.025);
        opacity: 1;
    }

    100% {
        transform: scale(1);
        opacity: .9;
    }
}

.listening #orb {
    box-shadow:
        0 0 35px rgba(0,242,254,.75),
        0 0 100px rgba(0,242,254,.3),
        inset 0 0 35px rgba(0,242,254,.25);
}

.processing #orb {
    animation: processingPulse 1s infinite ease-in-out;
}

.speaking #orb {
    animation: speakingPulse .7s infinite ease-in-out;
}

@keyframes processingPulse {
    0%, 100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.055);
    }
}

@keyframes speakingPulse {
    0%, 100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.07);
    }
}

</style>
</head>

<body>

<div id="container">

    <div id="orb">
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

(function() {

    const Streamlit = window.parent.Streamlit;

    const orb = document.getElementById("orb");
    const container = document.getElementById("container");
    const status = document.getElementById("status");

    let recorder = null;
    let stream = null;
    let analyser = null;
    let audioContext = null;

    let listening = false;
    let processing = false;
    let speaking = false;
    let sending = false;

    let silenceStart = null;
    let startedAt = 0;

    let animationFrame = null;

    let lastPlayedId = null;

    function statusText(text) {
        status.textContent = text;
    }

    function mode(name) {

        container.classList.remove(
            "listening",
            "processing",
            "speaking"
        );

        if (name) {
            container.classList.add(name);
        }
    }

    async function unlockAudio() {

        try {

            const AudioContextClass =
                window.AudioContext ||
                window.webkitAudioContext;

            if (!audioContext) {
                audioContext = new AudioContextClass();
            }

            if (audioContext.state === "suspended") {
                await audioContext.resume();
            }

            const buffer =
                audioContext.createBuffer(
                    1,
                    1,
                    audioContext.sampleRate
                );

            const source =
                audioContext.createBufferSource();

            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);

        } catch (error) {
            console.log(error);
        }
    }

    function makeId() {

        return (
            Date.now().toString(36) +
            "-" +
            Math.random().toString(36).substring(2)
        );
    }

    async function startListening() {

        if (
            listening ||
            processing ||
            speaking ||
            sending
        ) {
            return;
        }

        await unlockAudio();

        try {

            stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

            let mimeType = "";

            if (
                MediaRecorder.isTypeSupported(
                    "audio/webm;codecs=opus"
                )
            ) {
                mimeType = "audio/webm;codecs=opus";
            } else if (
                MediaRecorder.isTypeSupported("audio/webm")
            ) {
                mimeType = "audio/webm";
            } else if (
                MediaRecorder.isTypeSupported("audio/mp4")
            ) {
                mimeType = "audio/mp4";
            }

            if (mimeType) {
                recorder =
                    new MediaRecorder(
                        stream,
                        { mimeType: mimeType }
                    );
            } else {
                recorder =
                    new MediaRecorder(stream);
            }

            const chunks = [];

            recorder.ondataavailable = function(event) {

                if (
                    event.data &&
                    event.data.size > 0
                ) {
                    chunks.push(event.data);
                }
            };

            recorder.onstop = function() {

                clearInterval();

                if (animationFrame) {
                    cancelAnimationFrame(animationFrame);
                    animationFrame = null;
                }

                if (stream) {

                    stream
                        .getTracks()
                        .forEach(function(track) {
                            track.stop();
                        });

                    stream = null;
                }

                listening = false;

                if (!chunks.length) {

                    mode("");
                    statusText("VOICE CORE ONLINE");
                    return;
                }

                const blob =
                    new Blob(
                        chunks,
                        {
                            type:
                                mimeType ||
                                "audio/webm"
                        }
                    );

                const reader =
                    new FileReader();

                reader.onloadend = function() {

                    if (sending) {
                        return;
                    }

                    sending = true;
                    processing = true;

                    mode("processing");
                    statusText("NEURAL RESPONSE");

                    const data =
                        reader.result;

                    const base64 =
                        data.split(",")[1];

                    Streamlit.setComponentValue({
                        id: makeId(),
                        audio: base64
                    });
                };

                reader.readAsDataURL(blob);
            };

            recorder.start();

            listening = true;
            startedAt = Date.now();
            silenceStart = null;

            mode("listening");
            statusText("LISTENING");

            const AudioContextClass =
                window.AudioContext ||
                window.webkitAudioContext;

            if (!audioContext) {
                audioContext = new AudioContextClass();
            }

            if (audioContext.state === "suspended") {
                await audioContext.resume();
            }

            const source =
                audioContext.createMediaStreamSource(
                    stream
                );

            analyser =
                audioContext.createAnalyser();

            analyser.fftSize = 2048;

            source.connect(analyser);

            const data =
                new Uint8Array(
                    analyser.fftSize
                );

            function detectSilence() {

                if (!listening) {
                    return;
                }

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

                const elapsed =
                    Date.now() - startedAt;

                if (
                    elapsed > 800 &&
                    rms < 0.045
                ) {

                    if (!silenceStart) {
                        silenceStart = Date.now();
                    }

                    if (
                        Date.now() - silenceStart >= 1500
                    ) {
                        stopListening();
                        return;
                    }

                } else {

                    silenceStart = null;
                }

                animationFrame =
                    requestAnimationFrame(
                        detectSilence
                    );
            }

            animationFrame =
                requestAnimationFrame(
                    detectSilence
                );

        } catch (error) {

            console.log(error);

            listening = false;
            processing = false;
            sending = false;

            mode("");
            statusText("MICROPHONE ERROR");

            setTimeout(function() {
                statusText("VOICE CORE ONLINE");
            }, 2500);
        }
    }

    function clearInterval() {
        silenceStart = null;
    }

    function stopListening() {

        if (!recorder) {
            return;
        }

        if (recorder.state !== "inactive") {
            recorder.stop();
        }
    }

    async function playAudio(base64, playId) {

        if (
            !base64 ||
            !playId ||
            playId === lastPlayedId
        ) {
            return;
        }

        lastPlayedId = playId;

        processing = false;
        sending = false;
        speaking = true;

        mode("speaking");
        statusText("SPEAKING");

        try {

            const AudioContextClass =
                window.AudioContext ||
                window.webkitAudioContext;

            if (!audioContext) {
                audioContext = new AudioContextClass();
            }

            if (audioContext.state === "suspended") {
                await audioContext.resume();
            }

            const binary =
                atob(base64);

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

            const buffer =
                await audioContext.decodeAudioData(
                    bytes.buffer
                );

            const source =
                audioContext.createBufferSource();

            source.buffer = buffer;
            source.connect(audioContext.destination);

            source.onended = function() {

                speaking = false;
                sending = false;

                mode("");
                statusText("VOICE CORE ONLINE");
            };

            source.start(0);

        } catch (error) {

            console.log(error);

            speaking = false;
            sending = false;

            mode("");
            statusText("VOICE CORE ONLINE");
        }
    }

    function handleRender(event) {

        const data = event.data;

        if (
            !data ||
            data.type !== "streamlit:render"
        ) {
            return;
        }

        const args =
            data.args || {};

        if (
            args.audio &&
            args.play_id
        ) {
            playAudio(
                args.audio,
                args.play_id
            );
        }

        if (
            args.state === "ready" &&
            !listening &&
            !processing &&
            !speaking
        ) {
            mode("");
            statusText("VOICE CORE ONLINE");
        }

        if (args.state === "error") {

            listening = false;
            processing = false;
            sending = false;
            speaking = false;

            mode("");
            statusText("J.A.R.V.I.S. ERROR");
        }
    }

    orb.addEventListener(
        "click",
        startListening
    );

    window.addEventListener(
        "message",
        handleRender
    );

    Streamlit.setComponentReady();

    Streamlit.setFrameHeight(285);

})();

</script>

</body>
</html>
"""

with open(
    os.path.join(COMPONENT_DIR, "index.html"),
    "w",
    encoding="utf-8",
) as file:
    file.write(HTML)


# =========================================================
# ONLY ONE COMPONENT INSTANCE / ONE KEY
# =========================================================

jarvis_component = components.declare_component(
    "jarvis_voice_core",
    path=COMPONENT_DIR,
)


# =========================================================
# RENDER FRONTEND
# =========================================================

current_audio = st.session_state.pending_audio
current_play_id = st.session_state.pending_play_id
current_state = st.session_state.pending_state

incoming = jarvis_component(
    audio=current_audio,
    play_id=current_play_id,
    state=current_state,
    key="jarvis_main_component",
)

if current_audio is not None:

    st.session_state.pending_audio = None
    st.session_state.pending_play_id = None
    st.session_state.pending_state = "ready"


# =========================================================
# PROCESS AUDIO
# =========================================================

if isinstance(incoming, dict):

    request_id = incoming.get("id")
    audio_b64 = incoming.get("audio")

    if (
        request_id
        and audio_b64
        and request_id != st.session_state.last_request_id
        and not st.session_state.processing
    ):

        st.session_state.last_request_id = request_id
        st.session_state.processing = True

        temp_path = None

        try:

            audio_bytes = base64.b64decode(audio_b64)

            temp_path = os.path.join(
                tempfile.gettempdir(),
                "jarvis_input.webm",
            )

            with open(
                temp_path,
                "wb",
            ) as audio_file:
                audio_file.write(audio_bytes)

            # =================================================
            # GROQ SPEECH TO TEXT
            # =================================================

            with open(
                temp_path,
                "rb",
            ) as audio_file:

                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    response_format="text",
                )

            if isinstance(transcription, str):
                user_text = transcription.strip()
            else:
                user_text = str(transcription).strip()

            if not user_text:

                st.session_state.processing = False
                st.session_state.pending_state = "ready"

                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

                st.rerun()

            # =================================================
            # GROQ CHAT
            # =================================================

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
                max_tokens=250,
            )

            reply = completion.choices[0].message.content.strip()

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": reply,
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
                "Accept": "audio/mpeg",
            }

            payload = {
                "text": reply,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.8,
                    "style": 0.2,
                    "use_speaker_boost": True,
                },
            }

            eleven_response = requests.post(
                eleven_url,
                headers=headers,
                json=payload,
                timeout=60,
            )

            eleven_response.raise_for_status()

            tts_audio = base64.b64encode(
                eleven_response.content
            ).decode("utf-8")

            # =================================================
            # SEND AUDIO TO FRONTEND
            # =================================================

            st.session_state.pending_audio = tts_audio
            st.session_state.pending_play_id = str(uuid.uuid4())
            st.session_state.pending_state = "speak"
            st.session_state.processing = False

            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            st.rerun()

        except Exception as error:

            st.session_state.processing = False
            st.session_state.pending_audio = None
            st.session_state.pending_play_id = None
            st.session_state.pending_state = "error"

            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

            st.error("J.A.R.V.I.S. ERROR: " + str(error))
