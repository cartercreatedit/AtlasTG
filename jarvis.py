import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import base64
import requests
import tempfile
import json

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
# J.A.R.V.I.S. INTERFACE
# =========================================================

def jarvis_voice_component():

    component_html = r"""
    <div id="jarvis">
        <div id="orb">
            <div id="inner">✦</div>
        </div>

        <div id="name">J.A.R.V.I.S.</div>
        <div id="status">VOICE CORE ONLINE</div>
    </div>

    <style>

    html, body {
        margin: 0;
        padding: 0;
        background: transparent;
        overflow: hidden;
    }

    #jarvis {
        width: 100%;
        height: 330px;

        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;

        font-family: Arial, sans-serif;
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
        align-items: center;
        justify-content: center;

        cursor: pointer;

        animation: pulse 3s infinite;

        transition: transform .25s ease;
    }

    #orb:hover {
        transform: scale(1.04);
    }

    #orb.recording {
        animation: recording 1s infinite;

        box-shadow:
            0 0 25px #00f2fe,
            0 0 65px rgba(0,242,254,.9),
            inset 0 0 35px rgba(0,242,254,.7);
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
        align-items: center;
        justify-content: center;

        color: #00f2fe;

        font-size: 42px;

        text-shadow:
            0 0 15px #00f2fe;
    }

    #name {
        margin-top: 20px;

        color: #00f2fe;

        font-size: 20px;

        letter-spacing: 5px;

        text-shadow:
            0 0 10px rgba(0,242,254,.8);
    }

    #status {
        margin-top: 8px;

        color: rgba(0,242,254,.7);

        font-size: 11px;

        letter-spacing: 3px;
    }

    @keyframes pulse {

        0%, 100% {
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

        0%, 100% {
            transform: scale(1);
        }

        50% {
            transform: scale(1.06);
        }
    }

    @keyframes processing {

        0%, 100% {
            transform: scale(.97);
        }

        50% {
            transform: scale(1.03);
        }
    }

    </style>

    <script>

    const orb = document.getElementById("orb");
    const status = document.getElementById("status");

    let recorder = null;
    let chunks = [];

    let audioContext = null;
    let analyser = null;

    let silenceTimeout = null;
    let animationFrame = null;

    const SILENCE_THRESHOLD = 8;
    const SILENCE_DURATION = 1500;


    function setStatus(value) {
        status.textContent = value;
    }


    function finishRecording() {

        if (!recorder) {
            return;
        }

        if (recorder.state !== "inactive") {
            recorder.stop();
        }

        if (silenceTimeout) {
            clearTimeout(silenceTimeout);
            silenceTimeout = null;
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


    function monitorSilence() {

        if (!analyser || !recorder) {
            return;
        }

        const values =
            new Uint8Array(analyser.fftSize);

        analyser.getByteTimeDomainData(values);

        let total = 0;

        for (let i = 0; i < values.length; i++) {

            const value =
                values[i] - 128;

            total += value * value;
        }

        const rms =
            Math.sqrt(total / values.length);


        if (rms < SILENCE_THRESHOLD) {

            if (!silenceTimeout) {

                silenceTimeout = setTimeout(
                    finishRecording,
                    SILENCE_DURATION
                );
            }

        } else {

            if (silenceTimeout) {

                clearTimeout(silenceTimeout);
                silenceTimeout = null;
            }
        }


        animationFrame =
            requestAnimationFrame(
                monitorSilence
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

                        chunks.push(event.data);
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


                            window.parent.postMessage(
                                {
                                    type: "JARVIS_AUDIO",
                                    audio: base64
                                },
                                "*"
                            );
                        };


                    reader.readAsDataURL(blob);
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


            source.connect(analyser);


            recorder.start();


            orb.classList.add("recording");


            monitorSilence();


        } catch (error) {

            console.error(error);

            setStatus("MICROPHONE ERROR");

            orb.classList.remove("recording");
        }
    }


    orb.addEventListener(
        "click",
        startRecording
    );


    window.parent.postMessage(
        {
            type: "JARVIS_READY"
        },
        "*"
    );

    </script>
    """

    return components.html(
        component_html,
        height=330,
        scrolling=False
    )


# =========================================================
# VOICE UI
# =========================================================

voice_event = jarvis_voice_component()


# =========================================================
# AUDIO BRIDGE
# =========================================================

audio_bridge = """
<script>

window.addEventListener(
    "message",
    function(event) {

        if (
            !event.data ||
            event.data.type !== "JARVIS_AUDIO"
        ) {
            return;
        }

        window.parent.postMessage(
            event.data,
            "*"
        );
    }
);

</script>
"""

components.html(
    audio_bridge,
    height=1
)


# =========================================================
# STREAMLIT AUDIO INPUT FALLBACK / EVENT HANDLER
# =========================================================

if isinstance(voice_event, dict):

    audio_base64 = voice_event.get("audio")

    if audio_base64 and not st.session_state.processing:

        st.session_state.processing = True

        try:

            audio_bytes = base64.b64decode(
                audio_base64
            )


            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".webm"
            ) as temp_audio:

                temp_audio.write(audio_bytes)

                temp_audio_path = temp_audio.name


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
                os.remove(temp_audio_path)
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


                audio_out =
                    base64.b64encode(
                        response.content
                    ).decode("utf-8")


                safe_audio =
                    json.dumps(audio_out)


                components.html(
                    f"""
                    <script>

                    const audio =
                        new Audio(
                            "data:audio/mpeg;base64," +
                            {safe_audio}
                        );

                    audio.play().catch(
                        function(error) {{
                            console.error(
                                error
                            );
                        }}
                    );

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
