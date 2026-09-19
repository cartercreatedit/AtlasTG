import streamlit as st
import requests
import base64
import os
import tempfile

from groq import Groq


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered"
)

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"] {
    background: #000000 !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

footer {
    visibility: hidden;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# API KEYS
# ============================================================

GROQ_API_KEY = (
    st.secrets.get("GROQ_API_KEY")
    or os.getenv("GROQ_API_KEY")
)

ELEVEN_API_KEY = (
    st.secrets.get("ELEVEN_API_KEY")
    or os.getenv("ELEVEN_API_KEY")
)

ELEVEN_VOICE_ID = (
    st.secrets.get("ELEVEN_VOICE_ID")
    or "bfGb7JTLUnZebZRiFYyq"
)


if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing from your Streamlit secrets.")
    st.stop()

if not ELEVEN_API_KEY:
    st.error("ELEVEN_API_KEY is missing from your Streamlit secrets.")
    st.stop()


client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# MEMORY
# ============================================================

if "conversation" not in st.session_state:

    st.session_state.conversation = [
        {
            "role": "system",
            "content": """
You are J.A.R.V.I.S., an advanced artificial intelligence assistant.

You are loyal, professional, intelligent and concise.

Address Carter as "sir" or "Mr. Robinson".

Speak naturally because your responses will be converted into speech.

Keep responses short, normally 1-3 sentences.

Do not use markdown, bullet points, emojis, or formatting.
"""
        }
    ]


# ============================================================
# AUDIO THAT NEEDS TO BE PLAYED
# ============================================================

audio_to_play = st.session_state.pop(
    "audio_to_play",
    None
)


# ============================================================
# JARVIS COMPONENT
# ============================================================

jarvis_component = st.components.v2.component(

    "jarvis_voice_core",

    html="""

<div id="jarvis-container">

    <div id="core">

        <div id="inner-core">
            ✦
        </div>

    </div>


    <div id="jarvis-title">
        J.A.R.V.I.S.
    </div>


    <div id="jarvis-status">
        VOICE CORE ONLINE
    </div>

</div>

""",

    css="""

#jarvis-container {

    width: 100%;
    height: 650px;

    display: flex;
    flex-direction: column;

    align-items: center;
    justify-content: center;

    background: #000;

    font-family: Arial, sans-serif;

}


#core {

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


#inner-core {

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


#jarvis-title {

    margin-top: 30px;

    color: #00f2fe;

    font-family: Arial, sans-serif;

    font-size: 13px;

    letter-spacing: 3px;

    opacity: .75;

}


#jarvis-status {

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


#core.listening {

    border-color: #00f2fe;

    box-shadow:
        0 0 35px rgba(0,242,254,.7),
        0 0 90px rgba(0,242,254,.2),
        inset 0 0 35px rgba(0,242,254,.2);

}


#core.processing {

    animation:
        pulse .8s infinite ease-in-out;

}

""",

    js="""

export default function(component) {

    const {
        parentElement,
        setTriggerValue,
        data
    } = component;


    const core =
        parentElement.querySelector("#core");

    const status =
        parentElement.querySelector("#jarvis-status");


    let recorder = null;

    let chunks = [];

    let stream = null;

    let analyser = null;

    let audioContext = null;

    let silenceStart = null;

    let listening = false;


    const SILENCE_THRESHOLD = 8;

    const SILENCE_DURATION = 1500;


    // --------------------------------------------------------
    // PLAY JARVIS RESPONSE
    // --------------------------------------------------------

    if (data && data.audio) {

        try {

            const oldAudio =
                parentElement.querySelector(
                    "#jarvis-response-audio"
                );

            if (oldAudio) {
                oldAudio.remove();
            }


            const audio =
                document.createElement("audio");

            audio.id =
                "jarvis-response-audio";

            audio.src =
                "data:audio/mpeg;base64," +
                data.audio;

            audio.autoplay = true;

            audio.style.display = "none";


            parentElement.appendChild(audio);


            const playAudio = () => {

                audio.play().catch(
                    (error) => {
                        console.log(
                            "Autoplay prevented:",
                            error
                        );
                    }
                );

            };


            playAudio();

        } catch (error) {

            console.error(
                "Audio playback error:",
                error
            );

        }

    }


    // --------------------------------------------------------
    // AUDIO MONITOR
    // --------------------------------------------------------

    function monitorAudio() {

        if (!listening) {
            return;
        }


        if (!analyser) {
            return;
        }


        const dataArray =
            new Uint8Array(
                analyser.frequencyBinCount
            );


        analyser.getByteFrequencyData(
            dataArray
        );


        let total = 0;


        for (
            let i = 0;
            i < dataArray.length;
            i++
        ) {

            total += dataArray[i];

        }


        const average =
            total / dataArray.length;


        if (average < SILENCE_THRESHOLD) {

            if (silenceStart === null) {

                silenceStart =
                    Date.now();

            }

            else if (
                Date.now() -
                silenceStart >=
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

        if (listening) {
            return;
        }


        try {

            status.innerText =
                "LISTENING CORE ONLINE";


            chunks = [];

            silenceStart = null;

            stream =
                await navigator.mediaDevices
                    .getUserMedia({
                        audio: true
                    });


            let mimeType = "";


            const formats = [

                "audio/webm;codecs=opus",

                "audio/webm",

                "audio/mp4",

                "audio/ogg;codecs=opus"

            ];


            for (
                const format of formats
            ) {

                if (
                    MediaRecorder
                        .isTypeSupported(format)
                ) {

                    mimeType = format;

                    break;

                }

            }


            recorder =
                mimeType
                    ? new MediaRecorder(
                        stream,
                        { mimeType }
                    )
                    : new MediaRecorder(
                        stream
                    );


            recorder.ondataavailable =
                (event) => {

                    if (
                        event.data &&
                        event.data.size > 0
                    ) {

                        chunks.push(
                            event.data
                        );

                    }

                };


            recorder.onstop =
                async () => {

                    listening = false;


                    core.classList.remove(
                        "listening"
                    );

                    core.classList.add(
                        "processing"
                    );


                    status.innerText =
                        "PROCESSING NEURAL RESPONSE";


                    const finalMime =
                        recorder.mimeType ||
                        mimeType ||
                        "audio/webm";


                    const blob =
                        new Blob(
                            chunks,
                            {
                                type: finalMime
                            }
                        );


                    const reader =
                        new FileReader();


                    reader.onloadend =
                        () => {

                            try {

                                const result =
                                    reader.result;


                                const comma =
                                    result.indexOf(",");


                                if (comma === -1) {

                                    throw new Error(
                                        "Invalid audio data."
                                    );

                                }


                                const base64 =
                                    result.substring(
                                        comma + 1
                                    );


                                // THIS IS THE IMPORTANT FIX.
                                // Proper Streamlit V2
                                // JavaScript → Python event.

                                setTriggerValue(
                                    "audio",
                                    {
                                        base64: base64,
                                        mime_type:
                                            finalMime
                                    }
                                );


                            } catch (error) {

                                console.error(
                                    error
                                );

                                status.innerText =
                                    "AUDIO TRANSFER ERROR";

                                core.classList.remove(
                                    "processing"
                                );

                            }

                        };


                    reader.readAsDataURL(
                        blob
                    );


                    if (stream) {

                        stream
                            .getTracks()
                            .forEach(
                                track =>
                                    track.stop()
                            );

                    }


                    if (audioContext) {

                        try {
                            await audioContext.close();
                        } catch (e) {}

                    }

                };


            recorder.start();


            listening = true;


            core.classList.add(
                "listening"
            );


            // Audio analyser for silence detection

            audioContext =
                new (
                    window.AudioContext ||
                    window.webkitAudioContext
                )();


            analyser =
                audioContext.createAnalyser();


            analyser.fftSize = 256;


            const source =
                audioContext
                    .createMediaStreamSource(
                        stream
                    );


            source.connect(
                analyser
            );


            monitorAudio();


        } catch (error) {

            console.error(
                "Microphone error:",
                error
            );


            status.innerText =
                "MICROPHONE ERROR";


            core.classList.remove(
                "listening"
            );

        }

    }


    // --------------------------------------------------------
    // STOP RECORDING
    // --------------------------------------------------------

    function stopRecording() {

        if (!recorder) {
            return;
        }


        if (
            recorder.state ===
            "recording"
        ) {

            recorder.stop();

        }

    }


    // --------------------------------------------------------
    // CLICK
    // --------------------------------------------------------

    core.onclick = () => {

        if (!listening) {

            startRecording();

        } else {

            stopRecording();

        }

    };


    // --------------------------------------------------------
    // CLEANUP
    // --------------------------------------------------------

    return () => {

        listening = false;


        if (
            recorder &&
            recorder.state === "recording"
        ) {

            recorder.stop();

        }


        if (stream) {

            stream
                .getTracks()
                .forEach(
                    track =>
                        track.stop()
                );

        }

    };

}

""",
)


# ============================================================
# MOUNT COMPONENT
# ============================================================

result = jarvis_component(
    data={
        "audio": audio_to_play
    },
    on_audio_change=lambda: None,
    key="jarvis_core"
)


# ============================================================
# RECEIVE AUDIO FROM JAVASCRIPT
# ============================================================

audio_event = result.audio


if audio_event:

    try:

        audio_base64 = audio_event["base64"]

        mime_type = audio_event.get(
            "mime_type",
            "audio/webm"
        )


        # ----------------------------------------------------
        # SAVE TEMP AUDIO
        # ----------------------------------------------------

        extension = ".webm"

        if "mp4" in mime_type:
            extension = ".mp4"

        elif "ogg" in mime_type:
            extension = ".ogg"


        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        )


        temp_path = temp_file.name


        temp_file.write(
            base64.b64decode(
                audio_base64
            )
        )


        temp_file.close()


        # ----------------------------------------------------
        # GROQ WHISPER
        # ----------------------------------------------------

        with open(
            temp_path,
            "rb"
        ) as audio_file:

            transcription =
                client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    response_format="text"
                )


        if isinstance(
            transcription,
            str
        ):

            user_text =
                transcription.strip()

        else:

            user_text =
                str(
                    getattr(
                        transcription,
                        "text",
                        transcription
                    )
                ).strip()


        # Delete recording

        try:

            os.remove(
                temp_path
            )

        except OSError:

            pass


        if not user_text:

            st.rerun()


        # ----------------------------------------------------
        # JARVIS RESPONSE
        # ----------------------------------------------------

        st.session_state.conversation.append(
            {
                "role": "user",
                "content": user_text
            }
        )


        completion =
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=
                    st.session_state.conversation[-8:],
                temperature=0.3,
                max_tokens=200
            )


        # IMPORTANT FIX:
        # choices is a list.

        reply =
            completion.choices[0].message.content.strip()


        st.session_state.conversation.append(
            {
                "role": "assistant",
                "content": reply
            }
        )


        # ----------------------------------------------------
        # ELEVENLABS
        # ----------------------------------------------------

        eleven_url =
            (
                "https://api.elevenlabs.io/v1/"
                "text-to-speech/"
                + ELEVEN_VOICE_ID
            )


        headers = {
            "xi-api-key": ELEVEN_API_KEY,
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


        response =
            requests.post(
                eleven_url,
                headers=headers,
                json=payload,
                timeout=60
            )


        if not response.ok:

            st.error(
                "ElevenLabs error: "
                + response.text
            )

            st.stop()


        # ----------------------------------------------------
        # SEND AUDIO BACK TO JAVASCRIPT
        # ----------------------------------------------------

        st.session_state.audio_to_play =
            base64.b64encode(
                response.content
            ).decode("utf-8")


        # Rerun so V2 component receives the audio
        st.rerun()


    except Exception as error:

        st.error(
            "J.A.R.V.I.S. error: "
            + str(error)
        )
