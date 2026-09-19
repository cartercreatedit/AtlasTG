import streamlit as st
import requests
import base64
import os
import tempfile
import streamlit.components.v2 as components
from groq import Groq


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
)


# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]

ELEVEN_VOICE_ID = st.secrets.get(
    "ELEVEN_VOICE_ID",
    "bfGb7JTLUnZebZRiFYyq",
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
                "Keep spoken responses short and natural. "
                "Do not use markdown, bullet points, or unnecessary formatting."
            ),
        }
    ]

if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

if "processing" not in st.session_state:
    st.session_state.processing = False


# =========================================================
# J.A.R.V.I.S. VOICE COMPONENT
# =========================================================

JARVIS_HTML = """
<div id="jarvis-container">

    <div id="orb" style="
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
    ">

        <div style="
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
        ">
            ✦
        </div>

    </div>

    <div style="
        margin-top:30px;
        color:#00f2fe;
        font-family:Arial,sans-serif;
        font-size:13px;
        letter-spacing:3px;
        opacity:.75;
    ">
        J.A.R.V.I.S.
    </div>

    <div id="status" style="
        margin-top:10px;
        color:#777;
        font-family:Arial,sans-serif;
        font-size:11px;
        letter-spacing:2px;
    ">
        VOICE CORE ONLINE
    </div>

</div>
"""

JARVIS_CSS = """
#jarvis-container {
    width: 100%;
    min-height: 310px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: transparent;
    font-family: Arial, sans-serif;
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

#orb.recording {
    box-shadow:
        0 0 35px rgba(0,242,254,.55),
        0 0 90px rgba(0,242,254,.22),
        inset 0 0 35px rgba(0,242,254,.2);
}

#orb.processing {
    animation: pulse 1s infinite ease-in-out;
}

#status {
    transition: opacity .2s ease;
}
"""

JARVIS_JS = """
export default function(component) {

    const {
        parentElement,
        setTriggerValue,
        data
    } = component;

    const orb = parentElement.querySelector("#orb");
    const status = parentElement.querySelector("#status");

    let mediaRecorder = null;
    let audioChunks = [];
    let audioContext = null;
    let analyser = null;
    let microphone = null;
    let animationFrame = null;
    let silenceStart = null;
    let isRecording = false;
    let stream = null;

    const SILENCE_THRESHOLD = 8;
    const SILENCE_DURATION = 1500;

    function setStatus(text) {
        status.textContent = text;
    }

    function cleanupAudio() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }

        if (audioContext) {
            try {
                audioContext.close();
            } catch (e) {}
            audioContext = null;
        }

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }

        microphone = null;
        analyser = null;
    }

    function finishRecording() {

        if (!isRecording) {
            return;
        }

        isRecording = false;

        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }

        orb.classList.remove("recording");
        orb.classList.add("processing");
        setStatus("PROCESSING NEURAL RESPONSE");

        cleanupAudio();
    }

    function monitorSilence() {

        if (!isRecording || !analyser) {
            return;
        }

        const dataArray = new Uint8Array(analyser.fftSize);

        analyser.getByteTimeDomainData(dataArray);

        let sum = 0;

        for (let i = 0; i < dataArray.length; i++) {
            const value = dataArray[i] - 128;
            sum += value * value;
        }

        const rms = Math.sqrt(sum / dataArray.length);

        if (rms < SILENCE_THRESHOLD) {

            if (silenceStart === null) {
                silenceStart = Date.now();
            }

            if (Date.now() - silenceStart >= SILENCE_DURATION) {
                finishRecording();
                return;
            }

        } else {
            silenceStart = null;
        }

        animationFrame = requestAnimationFrame(monitorSilence);
    }

    async function startRecording() {

        if (isRecording) {
            return;
        }

        try {

            setStatus("INITIALIZING MICROPHONE");

            stream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            audioChunks = [];

            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = function(event) {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async function() {

                const audioBlob = new Blob(
                    audioChunks,
                    {
                        type: mediaRecorder.mimeType || "audio/webm"
                    }
                );

                const reader = new FileReader();

                reader.onloadend = function() {

                    const result = reader.result;

                    if (!result) {
                        setStatus("VOICE CORE ONLINE");
                        orb.classList.remove("processing");
                        return;
                    }

                    const base64 = result.split(",")[1];

                    setTriggerValue(
                        "audio",
                        {
                            base64: base64,
                            mime_type: audioBlob.type
                        }
                    );
                };

                reader.readAsDataURL(audioBlob);
            };

            audioContext = new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

            microphone = audioContext.createMediaStreamSource(stream);

            analyser = audioContext.createAnalyser();

            analyser.fftSize = 2048;
            analyser.smoothingTimeConstant = 0.8;

            microphone.connect(analyser);

            mediaRecorder.start();

            isRecording = true;
            silenceStart = null;

            orb.classList.add("recording");
            setStatus("LISTENING");

            monitorSilence();

        } catch (error) {

            console.error(error);

            setStatus("MICROPHONE ACCESS REQUIRED");
            orb.classList.remove("recording");
            orb.classList.remove("processing");

            cleanupAudio();
        }
    }

    orb.onclick = function() {

        if (isRecording) {
            finishRecording();
            return;
        }

        if (orb.classList.contains("processing")) {
            return;
        }

        startRecording();
    };


    // =====================================================
    // PLAY RESPONSE AUDIO
    // =====================================================

    if (data && data.audio) {

        try {

            const audioBytes = Uint8Array.from(
                atob(data.audio),
                function(character) {
                    return character.charCodeAt(0);
                }
            );

            const blob = new Blob(
                [audioBytes],
                {
                    type: "audio/mpeg"
                }
            );

            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);

            audio.onended = function() {
                URL.revokeObjectURL(audioUrl);
                orb.classList.remove("processing");
                setStatus("VOICE CORE ONLINE");
            };

            audio.onerror = function() {
                URL.revokeObjectURL(audioUrl);
                orb.classList.remove("processing");
                setStatus("VOICE CORE ONLINE");
            };

            audio.play().catch(function(error) {
                console.error("Autoplay blocked:", error);
                orb.classList.remove("processing");
                setStatus("VOICE CORE ONLINE");
            });

        } catch (error) {

            console.error(error);

            orb.classList.remove("processing");
            setStatus("VOICE CORE ONLINE");
        }
    }
}
"""


jarvis_component = components.v2.component(
    "jarvis_voice_core",
    html=JARVIS_HTML,
    css=JARVIS_CSS,
    js=JARVIS_JS,
)


# =========================================================
# SEND AUDIO BACK TO COMPONENT
# =========================================================

audio_to_play = st.session_state.audio_to_play
st.session_state.audio_to_play = None


# =========================================================
# MOUNT COMPONENT
# =========================================================

result = jarvis_component(
    data={
        "audio": audio_to_play
    },
    on_audio_change=lambda: None,
    key="jarvis_core",
)


# =========================================================
# PROCESS MICROPHONE AUDIO
# =========================================================

audio_event = result.audio

if audio_event and not st.session_state.processing:

    st.session_state.processing = True

    try:

        audio_base64 = audio_event.get("base64")

        if not audio_base64:
            raise ValueError("No audio data received.")

        audio_bytes = base64.b64decode(audio_base64)

        temp_audio_path = os.path.join(
            tempfile.gettempdir(),
            "jarvis_temp_audio.webm",
        )

        with open(temp_audio_path, "wb") as audio_file:
            audio_file.write(audio_bytes)

        # -------------------------------------------------
        # SPEECH TO TEXT
        # -------------------------------------------------

        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text",
            )

        if isinstance(transcription, str):
            user_text = transcription.strip()
        else:
            user_text = getattr(
                transcription,
                "text",
                str(transcription),
            ).strip()

        try:
            os.remove(temp_audio_path)
        except OSError:
            pass

        if not user_text:
            st.session_state.processing = False
            st.rerun()

        # -------------------------------------------------
        # ADD USER MESSAGE
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        # -------------------------------------------------
        # J.A.R.V.I.S. RESPONSE
        # -------------------------------------------------

        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=st.session_state.messages,
            temperature=0.3,
            max_tokens=200,
        )

        reply = completion.choices[0].message.content.strip()

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        # -------------------------------------------------
        # ELEVENLABS TEXT TO SPEECH
        # -------------------------------------------------

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
            },
        }

        response = requests.post(
            eleven_url,
            headers=eleven_headers,
            json=eleven_payload,
            timeout=60,
        )

        response.raise_for_status()

        st.session_state.audio_to_play = (
            base64.b64encode(response.content).decode("utf-8")
        )

    except Exception as error:

        st.error(f"J.A.R.V.I.S. ERROR: {error}")

    finally:

        st.session_state.processing = False

        st.rerun()
