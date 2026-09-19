import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

import os
import base64
import requests
import uuid


# ─────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ─────────────────────────────────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────────────────────────────────

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
    or "bfGb7JTLUnZebZRiFYyq"
)


if not groq_key:
    st.error("Missing GROQ_API_KEY inside Secrets.")
    st.stop()

if not eleven_key:
    st.error("Missing ELEVEN_API_KEY inside Secrets.")
    st.stop()

if not voice_id:
    st.error("Missing ELEVEN_VOICE_ID inside Secrets.")
    st.stop()


client = Groq(api_key=groq_key)


# ─────────────────────────────────────────────────────────────────────
# MEMORY
# ─────────────────────────────────────────────────────────────────────

if "vox_history" not in st.session_state:
    st.session_state.vox_history = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a hyper-advanced artificial "
                "intelligence system built exclusively by your creator, "
                "Carter Forester Robinson. You address him exclusively "
                "as sir or Mr. Robinson with absolute loyalty and respect. "
                "Your tone is sharp, highly logical, professional, "
                "sophisticated, and deeply loyal. Keep your responses "
                "short and punchy, 1 to 3 sentences max, so they sound "
                "like natural speech. Never use markdown symbols, headers, "
                "bold tags, or lists."
            )
        }
    ]


if "audio_tag" not in st.session_state:
    st.session_state.audio_tag = None


# ─────────────────────────────────────────────────────────────────────
# PLAY GENERATED VOICE AUTOMATICALLY
# ─────────────────────────────────────────────────────────────────────

if st.session_state.audio_tag:
    st.markdown(
        st.session_state.audio_tag,
        unsafe_allow_html=True
    )
    st.session_state.audio_tag = None


# ─────────────────────────────────────────────────────────────────────
# FULL SCREEN BLACK UI
# ─────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>

    .stApp, .main, .block-container {
        background-color: #000000 !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    #MainMenu, footer, header, .stDeployButton {
        visibility: hidden !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ─────────────────────────────────────────────────────────────────────
# FRONT-END J.A.R.V.I.S. CORE
# ─────────────────────────────────────────────────────────────────────

jarvis_frontend_html = """

<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<style>

body, html {
    background-color: #000000;
    margin: 0;
    padding: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;

    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}


.jarvis-sphere {

    width: 140px;
    height: 140px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(0,242,254,0.15) 0%,
            rgba(0,242,254,0) 70%
        );

    border: 2px solid #00f2fe;

    box-shadow:
        0 0 30px rgba(0,242,254,0.4),
        inset 0 0 20px rgba(0,242,254,0.2);

    cursor: pointer;

    transition:
        transform 0.05s ease,
        border-color 0.3s ease,
        box-shadow 0.3s ease;

    display: flex;
    justify-content: center;
    align-items: center;
}


.jarvis-sphere.recording {

    border-color: #ff416c;

    background:
        radial-gradient(
            circle,
            rgba(255,65,108,0.2) 0%,
            rgba(255,65,108,0) 70%
        );

    box-shadow:
        0 0 40px rgba(255,65,108,0.6),
        inset 0 0 25px rgba(255,65,108,0.3);
}


.status-indicator {

    margin-top: 32px;

    color: #00f2fe;

    font-size: 0.8rem;

    letter-spacing: 2px;

    text-transform: uppercase;

    opacity: 0.6;
}


.recording-text {
    color: #ff416c !important;
    opacity: 1 !important;
}

</style>

</head>


<body>


<div style="
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    width:100vw;
    height:100vh;
">

    <div
        class="jarvis-sphere"
        id="coreWidget"
    >

        <span
            id="coreIcon"
            style="
                color:#00f2fe;
                font-size:1.5rem;
                transition:color 0.3s;
            "
        >
            ✦
        </span>

    </div>


    <div
        class="status-indicator"
        id="statusLabel"
    >
        // TAP ONCE TO AWAKEN SYSTEM PROTOCOLS
    </div>

</div>


<script>


let mediaRecorder;

let audioChunks = [];

let isRecording = false;


let audioContext;

let analyser;

let dataArray;

let bufferLength;

let streamRef;


let silenceStart = null;

const SILENCE_THRESHOLD = 8;

const SILENCE_DURATION = 1500;


const sphereBtn =
    document.getElementById("coreWidget");

const statusLabel =
    document.getElementById("statusLabel");

const coreIcon =
    document.getElementById("coreIcon");



sphereBtn.onclick = async () => {


    if (!isRecording) {


        audioChunks = [];


        statusLabel.innerText =
            "// INITIALIZING CORE PROCESSORS...";


        try {


            const stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: true
                });


            streamRef = stream;


            /*
             * Pick a format the browser actually supports.
             */
            let mimeType = "";

            const possibleTypes = [
                "audio/webm;codecs=opus",
                "audio/webm",
                "audio/mp4",
                "audio/ogg;codecs=opus"
            ];


            for (const type of possibleTypes) {

                if (
                    MediaRecorder.isTypeSupported(type)
                ) {
                    mimeType = type;
                    break;
                }

            }


            mediaRecorder = mimeType
                ? new MediaRecorder(stream, { mimeType })
                : new MediaRecorder(stream);


            mediaRecorder.ondataavailable = (event) => {

                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }

            };


            mediaRecorder.onstop = () => {


                statusLabel.innerText =
                    "// PACKING AUDIO MATRIX...";


                const actualMimeType =
                    mediaRecorder.mimeType ||
                    mimeType ||
                    "audio/webm";


                const audioBlob =
                    new Blob(
                        audioChunks,
                        { type: actualMimeType }
                    );


                const reader =
                    new FileReader();


                reader.readAsDataURL(audioBlob);


                reader.onloadend = () => {


                    const result =
                        reader.result;


                    const base64Parts =
                        result.split(",");


                    if (base64Parts.length > 1) {


                        /*
                         * Send only the Base64 audio data
                         * back to Streamlit.
                         */

                        window.parent.postMessage(
                            {
                                type:
                                    "streamlit:setComponentValue",

                                value:
                                    base64Parts[1]
                            },
                            "*"
                        );

                    }

                };


                stream.getTracks().forEach(
                    track => track.stop()
                );


                sphereBtn.classList.remove(
                    "recording"
                );

                coreIcon.style.color =
                    "#00f2fe";

                statusLabel.classList.remove(
                    "recording-text"
                );

                statusLabel.innerText =
                    "// PROCESSING NEURAL RESPONSE...";

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


            bufferLength =
                analyser.frequencyBinCount;


            dataArray =
                new Uint8Array(bufferLength);


            statusLabel.innerText =
                "// LISTENING CORE ONLINE...";


            statusLabel.classList.add(
                "recording-text"
            );


            sphereBtn.classList.add(
                "recording"
            );


            coreIcon.style.color =
                "#ff416c";


            isRecording = true;


            silenceStart = Date.now();


            mediaRecorder.start();


            requestAnimationFrame(
                monitorAudioStreamLoop
            );


        } catch (err) {


            console.error(err);


            statusLabel.innerText =
                "// HARDWARE ERROR: MIC EXCEPTION";

        }


    } else {


        isRecording = false;


        if (
            mediaRecorder &&
            mediaRecorder.state === "recording"
        ) {

            mediaRecorder.stop();

        }

    }

};



function monitorAudioStreamLoop() {


    if (!isRecording) {
        return;
    }


    analyser.getByteFrequencyData(
        dataArray
    );


    let sum = 0;


    for (
        let i = 0;
        i < bufferLength;
        i++
    ) {

        sum += dataArray[i];

    }


    const average =
        sum / bufferLength;


    let scaleValue =
        1 + (average / 120);


    if (scaleValue > 1.45) {
        scaleValue = 1.45;
    }


    sphereBtn.style.transform =
        "scale(" + scaleValue + ")";


    if (average < SILENCE_THRESHOLD) {


        if (silenceStart === null) {

            silenceStart = Date.now();

        }

        else if (
            Date.now() - silenceStart >
            SILENCE_DURATION
        ) {


            isRecording = false;


            if (
                mediaRecorder &&
                mediaRecorder.state === "recording"
            ) {

                mediaRecorder.stop();

            }


            return;

        }


    } else {


        silenceStart = null;

    }


    requestAnimationFrame(
        monitorAudioStreamLoop
    );

}


</script>


</body>

</html>

"""


# ─────────────────────────────────────────────────────────────────────
# LOAD FRONT END
# ─────────────────────────────────────────────────────────────────────

incoming_audio_payload = components.html(
    jarvis_frontend_html,
    height=700,
    scrolling=False
)


# ─────────────────────────────────────────────────────────────────────
# BACK-END AUDIO PROCESSING
# ─────────────────────────────────────────────────────────────────────

if incoming_audio_payload:

    if isinstance(incoming_audio_payload, list):

        raw_b64 = (
            incoming_audio_payload[0]
            if len(incoming_audio_payload) > 0
            else ""
        )

    else:

        raw_b64 = incoming_audio_payload


    if raw_b64:


        try:

            # Decode browser audio
            audio_data = base64.b64decode(
                raw_b64
            )


            # Save temporary audio file
            temp_audio_path = "jarvis_temp.webm"


            with open(
                temp_audio_path,
                "wb"
            ) as audio_file:

                audio_file.write(
                    audio_data
                )


            # ─────────────────────────────────────────────
            # GROQ WHISPER TRANSCRIPTION
            # ─────────────────────────────────────────────

            with open(
                temp_audio_path,
                "rb"
            ) as audio_file:

                transcription = (
                    client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo",
                        file=audio_file,
                        response_format="text"
                    )
                )


            # Get the actual text safely
            if isinstance(
                transcription,
                str
            ):

                user_text = (
                    transcription.strip()
                )

            else:

                user_text = str(
                    getattr(
                        transcription,
                        "text",
                        transcription
                    )
                ).strip()


            # Delete temporary recording
            try:

                os.remove(
                    temp_audio_path
                )

            except OSError:

                pass


            # ─────────────────────────────────────────────
            # SEND TEXT TO J.A.R.V.I.S.
            # ─────────────────────────────────────────────

            if user_text:


                st.session_state.vox_history.append(
                    {
                        "role": "user",
                        "content": user_text
                    }
                )


                completion = (
                    client.chat.completions.create(
                        model="llama-3.3-70b-versatile",

                        messages=(
                            st.session_state
                            .vox_history[-6:]
                        ),

                        temperature=0.3,

                        max_tokens=200
                    )
                )


                # FIXED:
                # choices is a list
                reply = (
                    completion
                    .choices[0]
                    .message
                    .content
                    .strip()
                )


                st.session_state.vox_history.append(
                    {
                        "role": "assistant",
                        "content": reply
                    }
                )


                # ─────────────────────────────────────────
                # ELEVENLABS TEXT TO SPEECH
                # ─────────────────────────────────────────

                tts_url = (
                    "https://api.elevenlabs.io/v1/"
                    f"text-to-speech/{voice_id}"
                )


                headers = {
                    "xi-api-key": eleven_key,
                    "Content-Type": "application/json"
                }


                payload = {
                    "text": reply,

                    "model_id":
                        "eleven_multilingual_v2",

                    "voice_settings": {
                        "stability": 0.75,
                        "similarity_boost": 0.85
                    }
                }


                tts_response = requests.post(
                    tts_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )


                # ─────────────────────────────────────────
                # PLAY RESPONSE AUTOMATICALLY
                # ─────────────────────────────────────────

                if tts_response.ok:


                    audio_b64 = base64.b64encode(
                        tts_response.content
                    ).decode("utf-8")


                    audio_id = str(
                        uuid.uuid4()
                    )


                    st.session_state.audio_tag = (
                        f"""
                        <audio
                            id="{audio_id}"
                            autoplay
                            style="display:none;"
                        >
                            <source
                                src="data:audio/mpeg;base64,{audio_b64}"
                                type="audio/mpeg"
                            >
                        </audio>

                        <script>
                            const audio =
                                document.getElementById(
                                    "{audio_id}"
                                );

                            if (audio) {{
                                audio.play().catch(
                                    () => {{}}
                                );
                            }}
                        </script>
                        """
                    )


                else:


                    st.error(
                        "ElevenLabs error: "
                        + tts_response.text
                    )


                # Force Streamlit to rerun so the
                # generated audio is inserted.
                st.rerun()


        except Exception as error:


            # Make sure temporary file is removed
            try:

                if os.path.exists(
                    "jarvis_temp.webm"
                ):

                    os.remove(
                        "jarvis_temp.webm"
                    )

            except OSError:

                pass


            st.error(
                f"J.A.R.V.I.S. system error: {error}"
            )
