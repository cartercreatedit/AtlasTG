import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile
import uuid
import json

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

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a personal AI assistant for Carter "
                "Robinson. Address him naturally as sir when appropriate. "
                "Keep spoken answers concise and natural. Do not use markdown."
            ),
        }
    ]

if "processing" not in st.session_state:
    st.session_state.processing = False

if "request_id" not in st.session_state:
    st.session_state.request_id = None

if "tts_audio" not in st.session_state:
    st.session_state.tts_audio = None

if "tts_id" not in st.session_state:
    st.session_state.tts_id = None

if "frontend_state" not in st.session_state:
    st.session_state.frontend_state = "ready"


# =========================================================
# FRONTEND
# =========================================================

html = r"""
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
    justify-content:center;
    align-items:center;
}

#main {
    width:100%;
    height:100%;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}

#orb {
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
    user-select:none;
    -webkit-tap-highlight-color:transparent;
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
    min-height:14px;
    text-align:center;
}

@keyframes pulse {
    0% {
        transform:scale(1);
        opacity:.9;
    }
    50% {
        transform:scale(1.025);
        opacity:1;
    }
    100% {
        transform:scale(1);
        opacity:.9;
    }
}

.listening #orb {
    box-shadow:
        0 0 35px rgba(0,242,254,.75),
        0 0 100px rgba(0,242,254,.3),
        inset 0 0 35px rgba(0,242,254,.25);
}

.processing #orb {
    animation:processingPulse 1s infinite ease-in-out;
}

.speaking #orb {
    animation:speakingPulse .7s infinite ease-in-out;
}

@keyframes processingPulse {
    0%,100% {
        transform:scale(1);
    }
    50% {
        transform:scale(1.055);
    }
}

@keyframes speakingPulse {
    0%,100% {
        transform:scale(1);
    }
    50% {
        transform:scale(1.07);
    }
}
</style>
</head>

<body>

<div id="main">

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

    const orb = document.getElementById("orb");
    const main = document.getElementById("main");
    const status = document.getElementById("status");

    let recorder = null;
    let stream = null;
    let analyser = null;
    let audioContext = null;

    let listening = false;
    let sending = false;
    let speaking = false;

    let startedAt = 0;
    let silenceSince = null;
    let animationFrame = null;

    let lastAudioId = null;

    function setStatus(text) {
        status.textContent = text;
    }

    function setMode(mode) {

        main.classList.remove(
            "listening",
            "processing",
            "speaking"
        );

        if (mode) {
            main.classList.add(mode);
        }
    }

    function makeId() {

        return (
            Date.now().toString(36) +
            "-" +
            Math.random().toString(36).substring(2)
        );
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

    async function startListening() {

        if (
            listening ||
            sending ||
            speaking
        ) {
            return;
        }

        await unlockAudio();

        try {

            stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation:true,
                        noiseSuppression:true,
                        autoGainControl:true
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
                        {mimeType:mimeType}
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

                    setMode("");
                    setStatus("VOICE CORE ONLINE");
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

                    setMode("processing");
                    setStatus("NEURAL RESPONSE");

                    const result =
                        reader.result;

                    const audioBase64 =
                        result.split(",")[1];

                    /*
                     * Send the result directly to the
                     * Streamlit parent window.
                     */
                    window.parent.postMessage(
                        {
                            type:"jarvis_audio",
                            id:makeId(),
                            audio:audioBase64
                        },
                        "*"
                    );
                };

                reader.readAsDataURL(blob);
            };

            recorder.start();

            listening = true;
            startedAt = Date.now();
            silenceSince = null;

            setMode("listening");
            setStatus("LISTENING");

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

            function checkSilence() {

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

                    if (!silenceSince) {
                        silenceSince = Date.now();
                    }

                    if (
                        Date.now() - silenceSince >= 1500
                    ) {
                        stopListening();
                        return;
                    }

                } else {

                    silenceSince = null;
                }

                animationFrame =
                    requestAnimationFrame(
                        checkSilence
                    );
            }

            animationFrame =
                requestAnimationFrame(
                    checkSilence
                );

        } catch (error) {

            console.log(error);

            listening = false;
            sending = false;

            setMode("");
            setStatus("MICROPHONE ERROR");

            setTimeout(function() {
                setStatus("VOICE CORE ONLINE");
            },2500);
        }
    }

    function stopListening() {

        if (!recorder) {
            return;
        }

        if (recorder.state !== "inactive") {
            recorder.stop();
        }
    }

    async function playAudio(base64, id) {

        if (
            !base64 ||
            !id ||
            id === lastAudioId
        ) {
            return;
        }

        lastAudioId = id;

        sending = false;
        speaking = true;

        setMode("speaking");
        setStatus("SPEAKING");

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

            source.connect(
                audioContext.destination
            );

            source.onended = function() {

                speaking = false;
                sending = false;

                setMode("");
                setStatus("VOICE CORE ONLINE");
            };

            source.start(0);

        } catch (error) {

            console.log(error);

            speaking = false;
            sending = false;

            setMode("");
            setStatus("VOICE CORE ONLINE");
        }
    }

    /*
     * Listen for the Python side sending TTS audio.
     */
    window.addEventListener(
        "message",
        function(event) {

            const data = event.data;

            if (
                !data ||
                data.type !== "jarvis_tts"
            ) {
                return;
            }

            playAudio(
                data.audio,
                data.id
            );
        }
    );

    orb.addEventListener(
        "click",
        startListening
    );

    /*
     * Tell the Streamlit parent that this iframe
     * has loaded.
     */
    window.parent.postMessage(
        {
            type:"jarvis_ready"
        },
        "*"
    );

})();

</script>

</body>
</html>
"""

components.html(
    html,
    height=285,
    scrolling=False,
)


# =========================================================
# RECEIVE AUDIO FROM FRONTEND
# =========================================================

receiver_html = """
<script>
window.parent.postMessage(
    {
        type: "jarvis_receiver_ready"
    },
    "*"
);
</script>
"""

components.html(
    receiver_html,
    height=0,
    scrolling=False,
)


# =========================================================
# PROCESS USING STREAMLIT QUERY PARAMETER BRIDGE
# =========================================================

# Hidden bridge using browser local storage.
bridge = components.html(
    """
<script>
(function() {

    window.addEventListener("message", function(event) {

        if (
            event.data &&
            event.data.type === "jarvis_audio"
        ) {

            try {

                window.parent.localStorage.setItem(
                    "jarvis_audio_payload",
                    JSON.stringify(event.data)
                );

                window.parent.location.reload();

            } catch (e) {
                console.log(e);
            }
        }

    });

})();
</script>
""",
    height=0,
    scrolling=False,
)


# =========================================================
# READ PAYLOAD
# =========================================================

payload = None

try:

    payload = st.query_params.get("jarvis_audio")

    if payload:
        payload = json.loads(payload)

except Exception:
    payload = None


# =========================================================
# TTS DELIVERY
# =========================================================

if st.session_state.tts_audio:

    tts_payload = {
        "type": "jarvis_tts",
        "id": st.session_state.tts_id,
        "audio": st.session_state.tts_audio,
    }

    tts_json = json.dumps(tts_payload)

    components.html(
        f"""
        <script>
        window.parent.postMessage(
            {tts_json},
            "*"
        );
        </script>
        """,
        height=0,
        scrolling=False,
    )

    st.session_state.tts_audio = None
    st.session_state.tts_id = None


# =========================================================
# PROCESS NEW REQUEST
# =========================================================

if (
    isinstance(payload, dict)
    and payload.get("id")
    and payload.get("audio")
):

    request_id = payload["id"]

    if (
        request_id != st.session_state.request_id
        and not st.session_state.processing
    ):

        st.session_state.request_id = request_id
        st.session_state.processing = True

        temp_path = None

        try:

            audio_bytes = base64.b64decode(
                payload["audio"]
            )

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
            # TRANSCRIPTION
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

            if isinstance(
                transcription,
                str
            ):
                user_text = transcription.strip()
            else:
                user_text = str(
                    transcription
                ).strip()

            if not user_text:

                st.session_state.processing = False

                if (
                    temp_path
                    and os.path.exists(temp_path)
                ):
                    os.remove(temp_path)

                st.rerun()

            # =================================================
            # CHAT
            # =================================================

            st.session_state.messages.append(
                {
                    "role":"user",
                    "content":user_text,
                }
            )

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=st.session_state.messages,
                temperature=0.3,
                max_tokens=250,
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
                    "content":reply,
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
                "xi-api-key":ELEVEN_API_KEY,
                "Content-Type":"application/json",
                "Accept":"audio/mpeg",
            }

            body = {
                "text":reply,
                "model_id":"eleven_multilingual_v2",
                "voice_settings":{
                    "stability":0.45,
                    "similarity_boost":0.8,
                    "style":0.2,
                    "use_speaker_boost":True,
                },
            }

            response = requests.post(
                eleven_url,
                headers=headers,
                json=body,
                timeout=60,
            )

            response.raise_for_status()

            audio_base64 = base64.b64encode(
                response.content
            ).decode("utf-8")

            st.session_state.tts_audio = audio_base64
            st.session_state.tts_id = str(
                uuid.uuid4()
            )

            st.session_state.processing = False

            if (
                temp_path
                and os.path.exists(temp_path)
            ):
                os.remove(temp_path)

            st.query_params.clear()

            st.rerun()

        except Exception as error:

            st.session_state.processing = False

            if (
                temp_path
                and os.path.exists(temp_path)
            ):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

            st.error(
                "J.A.R.V.I.S. ERROR: "
                + str(error)
            )
