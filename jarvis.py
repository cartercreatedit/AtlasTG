import streamlit as st
from groq import Groq
import os
import base64
import json
import tempfile
import requests

# ============================================================
# J.A.R.V.I.S. — VOICE AI CORE
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# API KEYS
# ============================================================

groq_key = (
    st.secrets.get("GROQ_API_KEY")
    or os.getenv("GROQ_API_KEY")
    or ""
)

eleven_key = (
    st.secrets.get("ELEVEN_API_KEY")
    or os.getenv("ELEVEN_API_KEY")
    or ""
)

voice_id = (
    st.secrets.get("ELEVEN_VOICE_ID")
    or os.getenv("ELEVEN_VOICE_ID")
    or ""
)

if not groq_key:
    st.error("Missing GROQ_API_KEY.")
    st.stop()

if not eleven_key:
    st.error("Missing ELEVEN_API_KEY.")
    st.stop()

if not voice_id:
    st.error("Missing ELEVEN_VOICE_ID.")
    st.stop()

client = Groq(api_key=groq_key)

# ============================================================
# SESSION MEMORY
# ============================================================

if "vox_history" not in st.session_state:
    st.session_state.vox_history = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a highly advanced artificial "
                "intelligence assistant built by your creator, Carter "
                "Forester Robinson. Address him as sir or Mr. Robinson. "
                "Your personality is sharp, logical, professional, "
                "sophisticated and loyal. Keep responses short and natural "
                "for spoken conversation, usually one to three sentences. "
                "Do not use markdown, lists, emojis or headings."
            ),
        }
    ]

if "tts_audio" not in st.session_state:
    st.session_state.tts_audio = None

if "status" not in st.session_state:
    st.session_state.status = "READY"

# ============================================================
# FULLSCREEN DARK UI
# ============================================================

st.markdown(
    """
    <style>
    .stApp,
    .main,
    .block-container {
        background-color: #000000 !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100vw !important;
        min-height: 100vh !important;
        overflow: hidden !important;
    }

    #MainMenu,
    footer,
    header,
    .stDeployButton {
        visibility: hidden !important;
    }

    iframe {
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# JARVIS FRONTEND
# ============================================================

JARVIS_HTML = """
<div id="jarvis-root">
    <div id="sphere">
        <span id="icon">✦</span>
    </div>

    <div id="status">
        // TAP ONCE TO AWAKEN SYSTEM
    </div>

    <audio id="ttsAudio" playsinline></audio>
</div>
"""

JARVIS_CSS = """
#jarvis-root {
    width: 100%;
    height: 700px;
    background: #000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    overflow: hidden;
}

#sphere {
    width: 140px;
    height: 140px;
    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(0,242,254,0.18) 0%,
            rgba(0,242,254,0.02) 45%,
            rgba(0,242,254,0) 72%
        );

    border: 2px solid #00f2fe;

    box-shadow:
        0 0 30px rgba(0,242,254,0.4),
        inset 0 0 20px rgba(0,242,254,0.2);

    display: flex;
    justify-content: center;
    align-items: center;

    cursor: pointer;

    transition:
        transform 0.05s ease,
        border-color 0.3s ease,
        box-shadow 0.3s ease;
}

#sphere.recording {
    border-color: #ff416c;

    background:
        radial-gradient(
            circle,
            rgba(255,65,108,0.22) 0%,
            rgba(255,65,108,0.02) 50%,
            rgba(255,65,108,0) 75%
        );

    box-shadow:
        0 0 45px rgba(255,65,108,0.65),
        inset 0 0 25px rgba(255,65,108,0.3);
}

#sphere.processing {
    border-color: #a855f7;

    box-shadow:
        0 0 45px rgba(168,85,247,0.65),
        inset 0 0 25px rgba(168,85,247,0.3);
}

#icon {
    color: #00f2fe;
    font-size: 30px;
    transition: color 0.3s ease;
}

#status {
    margin-top: 32px;
    color: #00f2fe;
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.7;
    text-align: center;
}

#status.recording {
    color: #ff416c;
    opacity: 1;
}

#status.processing {
    color: #a855f7;
    opacity: 1;
}
"""

JARVIS_JS = """
export default function(component) {

    const {
        parentElement,
        setTriggerValue,
        data
    } = component;

    const sphere = parentElement.querySelector("#sphere");
    const icon = parentElement.querySelector("#icon");
    const status = parentElement.querySelector("#status");
    const audio = parentElement.querySelector("#ttsAudio");

    let mediaRecorder = null;
    let audioChunks = [];
    let recording = false;

    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let stream = null;

    let silenceStart = null;

    const SILENCE_THRESHOLD = 8;
    const SILENCE_DURATION = 1500;

    // --------------------------------------------------------
    // STATUS
    // --------------------------------------------------------

    function setStatus(text, mode = "") {
        status.textContent = text;

        status.classList.remove(
            "recording",
            "processing"
        );

        sphere.classList.remove(
            "recording",
            "processing"
        );

        if (mode) {
            status.classList.add(mode);
            sphere.classList.add(mode);
        }
    }

    // --------------------------------------------------------
    // FIND A RECORDING FORMAT THE BROWSER SUPPORTS
    // --------------------------------------------------------

    function getMimeType() {

        const formats = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/mp4",
            "audio/ogg;codecs=opus"
        ];

        for (const format of formats) {
            if (
                typeof MediaRecorder !== "undefined" &&
                MediaRecorder.isTypeSupported(format)
            ) {
                return format;
            }
        }

        return "";
    }

    // --------------------------------------------------------
    // STOP RECORDING
    // --------------------------------------------------------

    function stopRecording() {

        if (!recording) return;

        recording = false;

        if (
            mediaRecorder &&
            mediaRecorder.state === "recording"
        ) {
            mediaRecorder.stop();
        }

        if (stream) {
            stream.getTracks().forEach(
                track => track.stop()
            );
        }

        if (audioContext) {
            try {
                audioContext.close();
            } catch (e) {}
        }

        sphere.style.transform = "scale(1)";
    }

    // --------------------------------------------------------
    // MONITOR AUDIO / SILENCE
    // --------------------------------------------------------

    function monitorAudio() {

        if (!recording || !analyser) {
            return;
        }

        analyser.getByteFrequencyData(dataArray);

        let sum = 0;

        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }

        const average =
            sum / dataArray.length;

        let scale =
            1 + average / 120;

        if (scale > 1.45) {
            scale = 1.45;
        }

        sphere.style.transform =
            `scale(${scale})`;

        if (average < SILENCE_THRESHOLD) {

            if (silenceStart === null) {
                silenceStart = Date.now();
            }

            else if (
                Date.now() - silenceStart >
                SILENCE_DURATION
            ) {
                stopRecording();
                return;
            }

        } else {
            silenceStart = null;
        }

        requestAnimationFrame(
            monitorAudio
        );
    }

    // --------------------------------------------------------
    // START RECORDING
    // --------------------------------------------------------

    async function startRecording() {

        if (recording) return;

        try {

            setStatus(
                "// INITIALIZING MICROPHONE...",
                "recording"
            );

            stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

            const mimeType = getMimeType();

            if (!mimeType) {
                throw new Error(
                    "Browser does not support MediaRecorder."
                );
            }

            audioChunks = [];

            mediaRecorder =
                new MediaRecorder(
                    stream,
                    { mimeType }
                );

            mediaRecorder.ondataavailable =
                event => {

                    if (event.data.size > 0) {
                        audioChunks.push(
                            event.data
                        );
                    }
                };

            mediaRecorder.onstop = async () => {

                setStatus(
                    "// PROCESSING AUDIO...",
                    "processing"
                );

                const blob =
                    new Blob(
                        audioChunks,
                        { type: mimeType }
                    );

                const reader =
                    new FileReader();

                reader.onloadend = () => {

                    const dataUrl =
                        reader.result;

                    const comma =
                        dataUrl.indexOf(",");

                    const encoded =
                        dataUrl.substring(
                            comma + 1
                        );

                    const payload = {
                        base64: encoded,
                        mime_type: mimeType
                    };

                    setTriggerValue(
                        "audio",
                        payload
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

            const source =
                audioContext.createMediaStreamSource(
                    stream
                );

            source.connect(analyser);

            analyser.fftSize = 256;

            dataArray =
                new Uint8Array(
                    analyser.frequencyBinCount
                );

            recording = true;

            silenceStart = null;

            sphere.classList.add("recording");
            status.classList.add("recording");

            icon.style.color = "#ff416c";

            setStatus(
                "// LISTENING...",
                "recording"
            );

            mediaRecorder.start();

            requestAnimationFrame(
                monitorAudio
            );

        } catch (error) {

            console.error(error);

            setStatus(
                "// MICROPHONE ERROR"
            );

            icon.style.color =
                "#00f2fe";

            recording = false;
        }
    }

    // --------------------------------------------------------
    // SPHERE CLICK
    // --------------------------------------------------------

    sphere.onclick = async () => {

        if (recording) {
            stopRecording();
        } else {
            await startRecording();
        }
    };

    // --------------------------------------------------------
    // PLAY ELEVENLABS RESPONSE
    // --------------------------------------------------------

    if (
        data &&
        data.audio &&
        data.audio_id
    ) {

        const source =
            `data:audio/mpeg;base64,${data.audio}`;

        if (
            audio.dataset.audioId !==
            String(data.audio_id)
        ) {

            audio.dataset.audioId =
                String(data.audio_id);

            audio.src = source;

            setStatus(
                "// J.A.R.V.I.S. ONLINE"
            );

            icon.style.color =
                "#00f2fe";

            sphere.classList.remove(
                "processing"
            );

            audio.play().catch(
                error => {
                    console.warn(
                        "Autoplay blocked:",
                        error
                    );
                }
            );
        }
    }

    return () => {

        if (stream) {
            stream.getTracks().forEach(
                track => track.stop()
            );
        }

        if (audioContext) {
            try {
                audioContext.close();
            } catch (e) {}
        }
    };
}
"""

# ============================================================
# REGISTER STREAMLIT V2 COMPONENT
# ============================================================

jarvis_component = st.components.v2.component(
    "jarvis_voice_core",
    html=JARVIS_HTML,
    css=JARVIS_CSS,
    js=JARVIS_JS,
)

# ============================================================
# CURRENT AUDIO RESPONSE
# ============================================================

audio_b64 = None
audio_id = None

if st.session_state.tts_audio:

    audio_b64 = st.session_state.tts_audio["audio"]
    audio_id = st.session_state.tts_audio["id"]

# ============================================================
# MOUNT COMPONENT
# ============================================================

result = jarvis_component(
    data={
        "audio": audio_b64,
        "audio_id": audio_id,
    },
    default={
        "audio": None
    },
    on_audio_change=lambda: None,
)

# ============================================================
# RECEIVE AUDIO FROM JAVASCRIPT
# ============================================================

incoming_audio = None

try:
    incoming_audio = result.audio
except Exception:
    incoming_audio = None

# ============================================================
# PROCESS AUDIO
# ============================================================

if incoming_audio:

    try:

        # ----------------------------------------------------
        # Extract payload
        # ----------------------------------------------------

        if isinstance(
            incoming_audio,
            dict
        ):

            raw_b64 = incoming_audio.get(
                "base64",
                ""
            )

            mime_type = incoming_audio.get(
                "mime_type",
                "audio/webm"
            )

        else:

            raw_b64 = str(
                incoming_audio
            )

            mime_type = "audio/webm"

        if not raw_b64:
            st.stop()

        # ----------------------------------------------------
        # Decode audio
        # ----------------------------------------------------

        audio_data = base64.b64decode(
            raw_b64
        )

        # Determine file extension
        # from browser MIME type.
        # ----------------------------------------------------

        if "mp4" in mime_type:
            extension = ".mp4"

        elif "ogg" in mime_type:
            extension = ".ogg"

        elif "wav" in mime_type:
            extension = ".wav"

        else:
            extension = ".webm"

        # ----------------------------------------------------
        # Temporary audio file
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_audio:

            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # ----------------------------------------------------
        # GROQ WHISPER
        # ----------------------------------------------------

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

        try:
            os.remove(
                temp_audio_path
            )
        except OSError:
            pass

        # ----------------------------------------------------
        # Extract transcription
        # ----------------------------------------------------

        if isinstance(
            transcription,
            str
        ):
            user_text = transcription.strip()

        else:
            user_text = str(
                getattr(
                    transcription,
                    "text",
                    transcription
                )
            ).strip()

        # ----------------------------------------------------
        # Ignore empty recordings
        # ----------------------------------------------------

        if not user_text:
            st.rerun()

        # ----------------------------------------------------
        # Add user message
        # ----------------------------------------------------

        st.session_state.vox_history.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        # ----------------------------------------------------
        # GROQ CHAT
        # ----------------------------------------------------

        completion = (
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.vox_history[
                    -8:
                ],
                temperature=0.3,
                max_tokens=200,
            )
        )

        # IMPORTANT:
        # choices is a list.
        # ----------------------------------------------------

        reply = (
            completion
            .choices[0]
            .message
            .content
            .strip()
        )

        # ----------------------------------------------------
        # Save response
        # ----------------------------------------------------

        st.session_state.vox_history.append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        # ----------------------------------------------------
        # ELEVENLABS TTS
        # ----------------------------------------------------

        tts_url = (
            "https://api.elevenlabs.io/v1/"
            f"text-to-speech/{voice_id}"
        )

        headers = {
            "xi-api-key": eleven_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": reply,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.85,
            },
        }

        tts_response = requests.post(
            tts_url,
            headers=headers,
            json=payload,
            timeout=60,
        )

        # ----------------------------------------------------
        # Handle ElevenLabs errors
        # ----------------------------------------------------

        if not tts_response.ok:

            error_text = (
                tts_response.text[:500]
            )

            st.error(
                "ElevenLabs error: "
                + error_text
            )

            st.stop()

        # ----------------------------------------------------
        # Convert response to Base64
        # ----------------------------------------------------

        response_audio_b64 = base64.b64encode(
            tts_response.content
        ).decode("utf-8")

        # Unique ID makes the browser
        # play every new response.
        # ----------------------------------------------------

        audio_id = (
            str(
                hash(
                    response_audio_b64
                )
            )
        )

        st.session_state.tts_audio = {
            "audio": response_audio_b64,
            "id": audio_id,
        }

        # ----------------------------------------------------
        # Rerun so JS receives the audio
        # ----------------------------------------------------

        st.rerun()

    except Exception as error:

        st.error(
            f"J.A.R.V.I.S. processing error: {error}"
        )
