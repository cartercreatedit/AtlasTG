import streamlit as st
from groq import Groq
import datetime
import base64
import io

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================
# GROQ
# =========================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = ""

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# =========================
# SESSION STATE
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

if "speech_to_play" not in st.session_state:
    st.session_state.speech_to_play = ""

if "audio_event" not in st.session_state:
    st.session_state.audio_event = None


# =========================
# STYLE
# =========================

st.markdown("""
<style>

html, body, [class*="css"] {
    background: #0a0a0a !important;
}

.stApp {
    background: #0a0a0a;
    color: white;
}

.block-container {
    max-width: 760px;
    padding-top: 35px;
}

/* TITLE */

.jarvis-title {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 8px;
    color: white;
}

.jarvis-subtitle {
    text-align: center;
    color: #666;
    letter-spacing: 3px;
    margin-bottom: 25px;
}

/* CORE */

.core-container {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    margin-bottom: 20px;
}

.core-button {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 2px solid #00f2fe;
    display: flex;
    align-items: center;
    justify-content: center;

    box-shadow:
        0 0 15px #00f2fe,
        0 0 40px rgba(0,242,254,.25),
        inset 0 0 25px rgba(0,242,254,.15);

    cursor: pointer;
    transition: .2s;
}

.core-button:hover {
    transform: scale(1.03);
    box-shadow:
        0 0 25px #00f2fe,
        0 0 60px rgba(0,242,254,.35),
        inset 0 0 30px rgba(0,242,254,.2);
}

.inner-core {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    border: 2px solid #00f2fe;

    box-shadow:
        0 0 15px #00f2fe,
        inset 0 0 20px rgba(0,242,254,.25);
}

/* HIDE STREAMLIT COMPONENT WRAPPERS */

.voice-status {
    text-align: center;
    color: #777;
    font-size: 13px;
    margin-top: 15px;
    letter-spacing: 1px;
}

/* BUTTONS */

div.stButton > button {
    border-radius: 14px;
    height: 48px;
    background: #151515;
    border: 1px solid #333;
    color: white;
}

div.stButton > button:hover {
    border-color: #00f2fe;
    color: #00f2fe;
}

</style>
""", unsafe_allow_html=True)


# =========================
# CURRENT TIME
# =========================

now = datetime.datetime.now()

current_time = now.strftime("%I:%M %p")
current_date = now.strftime("%A, %B %d, %Y")


# =========================
# CUSTOM VOICE COMPONENT
# =========================

voice_component = st.components.v2.component(

    name="jarvis_hands_free_voice",

    html="""
    <div id="voice-ui"></div>
    """,

    css="""
    #voice-ui {
        width: 100%;
        height: 1px;
        overflow: hidden;
    }
    """,

    js="""

    export default function(component) {

        const {
            parentElement,
            data,
            setTriggerValue
        } = component;

        let stream = null;
        let recorder = null;
        let audioContext = null;
        let analyser = null;
        let animationFrame = null;

        let listening = false;
        let speechStarted = false;
        let silenceStart = null;

        let lastSpeech = "";
        let speaking = false;

        const SPEECH_THRESHOLD = 0.018;
        const SILENCE_TIME = 1200;
        const MIN_SPEECH_TIME = 350;

        let speechStartTime = null;


        // =========================
        // START MICROPHONE
        // =========================

        async function startListening() {

            if (listening || speaking) {
                return;
            }

            try {

                stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                recorder = new MediaRecorder(stream, {
                    mimeType: "audio/webm"
                });

                const chunks = [];

                recorder.ondataavailable = (event) => {

                    if (event.data.size > 0) {
                        chunks.push(event.data);
                    }

                };

                recorder.onstop = async () => {

                    listening = false;

                    if (animationFrame) {
                        cancelAnimationFrame(animationFrame);
                    }

                    if (stream) {
                        stream.getTracks().forEach(track => track.stop());
                    }

                    const blob = new Blob(
                        chunks,
                        { type: "audio/webm" }
                    );

                    if (blob.size < 1000) {
                        setTimeout(startListening, 300);
                        return;
                    }

                    const buffer = await blob.arrayBuffer();

                    const bytes = new Uint8Array(buffer);

                    let binary = "";

                    const chunkSize = 8192;

                    for (
                        let i = 0;
                        i < bytes.length;
                        i += chunkSize
                    ) {

                        const chunk = bytes.subarray(
                            i,
                            Math.min(i + chunkSize, bytes.length)
                        );

                        binary += String.fromCharCode(...chunk);

                    }

                    const base64 = btoa(binary);

                    setTriggerValue(
                        "audio",
                        base64
                    );
                };

                recorder.start();

                listening = true;
                speechStarted = false;
                silenceStart = null;
                speechStartTime = null;

                audioContext =
                    new (window.AudioContext ||
                    window.webkitAudioContext)();

                const source =
                    audioContext.createMediaStreamSource(stream);

                analyser =
                    audioContext.createAnalyser();

                analyser.fftSize = 512;

                source.connect(analyser);

                const dataArray =
                    new Uint8Array(analyser.fftSize);


                function detectSpeech() {

                    if (!listening) {
                        return;
                    }

                    analyser.getByteTimeDomainData(dataArray);

                    let sum = 0;

                    for (let i = 0; i < dataArray.length; i++) {

                        const value =
                            (dataArray[i] - 128) / 128;

                        sum += value * value;

                    }

                    const rms =
                        Math.sqrt(sum / dataArray.length);

                    const now = Date.now();

                    if (rms > SPEECH_THRESHOLD) {

                        if (!speechStarted) {

                            speechStarted = true;
                            speechStartTime = now;

                        }

                        silenceStart = null;

                    } else if (speechStarted) {

                        if (!silenceStart) {
                            silenceStart = now;
                        }

                        const speechDuration =
                            now - speechStartTime;

                        const silenceDuration =
                            now - silenceStart;

                        if (
                            speechDuration >= MIN_SPEECH_TIME &&
                            silenceDuration >= SILENCE_TIME
                        ) {

                            if (
                                recorder &&
                                recorder.state === "recording"
                            ) {
                                recorder.stop();
                            }

                            return;
                        }
                    }

                    animationFrame =
                        requestAnimationFrame(
                            detectSpeech
                        );
                }

                detectSpeech();

            } catch (error) {

                setTriggerValue(
                    "error",
                    String(error)
                );

            }
        }


        // =========================
        // SPEAK RESPONSE
        // =========================

        function speak(text) {

            if (!text) {
                setTimeout(startListening, 300);
                return;
            }

            if (!("speechSynthesis" in window)) {
                setTimeout(startListening, 300);
                return;
            }

            speaking = true;

            window.speechSynthesis.cancel();

            const utterance =
                new SpeechSynthesisUtterance(text);

            utterance.rate = 0.95;
            utterance.pitch = 0.9;
            utterance.volume = 1.0;

            utterance.onend = () => {

                speaking = false;

                setTimeout(
                    startListening,
                    250
                );

            };

            utterance.onerror = () => {

                speaking = false;

                setTimeout(
                    startListening,
                    250
                );

            };

            window.speechSynthesis.speak(
                utterance
            );
        }


        // =========================
        // PYTHON → JAVASCRIPT
        // =========================

        if (
            data &&
            data.speak &&
            data.speak !== lastSpeech
        ) {

            lastSpeech = data.speak;

            speak(data.speak);
        }


        // =========================
        // START WHEN ACTIVATED
        // =========================

        if (
            data &&
            data.active === true &&
            !listening &&
            !speaking
        ) {

            setTimeout(
                startListening,
                100
            );

        }


        // =========================
        // CLEANUP
        // =========================

        return () => {

            if (animationFrame) {
                cancelAnimationFrame(animationFrame);
            }

            if (stream) {
                stream.getTracks().forEach(
                    track => track.stop()
                );
            }

            if (audioContext) {
                audioContext.close();
            }

        };
    }

    """
)


# =========================
# AI
# =========================

def ask_jarvis(user_text):

    if not client:
        return "My Groq API key isn't connected."

    system_prompt = f"""
You are J.A.R.V.I.S., a personal AI assistant.

Current date:
{current_date}

Current time:
{current_time}

The user is speaking to you through a voice interface.

Speak naturally and conversationally.

Reply in the same language the user uses.

Keep responses reasonably concise because your response will be spoken aloud.

Do not use markdown.

Do not use bullet points unless absolutely necessary.

Do not describe your response as text.

Never claim you performed a computer action unless the application actually performed it.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(
        st.session_state.messages[-12:]
    )

    messages.append(
        {
            "role": "user",
            "content": user_text
        }
    )

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=messages,

            temperature=0.7,

            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"I encountered an error: {e}"


# =========================
# TRANSCRIBE
# =========================

def transcribe_audio(base64_audio):

    if not client:
        return None

    try:

        audio_bytes = base64.b64decode(
            base64_audio
        )

        result = client.audio.transcriptions.create(

            file=(
                "voice.webm",
                audio_bytes
            ),

            model="whisper-large-v3-turbo",

            response_format="json"
        )

        return result.text.strip()

    except Exception as e:

        st.error(
            f"Voice recognition error: {e}"
        )

        return None


# =========================
# HEADER
# =========================

st.markdown(
    '<div class="jarvis-title">J.A.R.V.I.S.</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="jarvis-subtitle">PERSONAL AI SYSTEM</div>',
    unsafe_allow_html=True
)


# =========================
# CORE
# =========================

st.markdown(
    """
    <div class="core-container">
        <div class="core-button">
            <div class="inner-core"></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# CONTROLS
# =========================

col1, col2, col3 = st.columns(3)

with col1:

    if st.button(
        "◉ ACTIVATE",
        use_container_width=True
    ):

        st.session_state.voice_active = True

        st.rerun()


with col2:

    if st.button(
        "TIME",
        use_container_width=True
    ):

        answer = (
            f"The current time is {current_time}."
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": "What time is it?"
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.session_state.speech_to_play = answer

        st.rerun()


with col3:

    if st.button(
        "CLEAR",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.speech_to_play = ""

        st.rerun()


# =========================
# VOICE COMPONENT
# =========================

component_data = {
    "active": st.session_state.voice_active,
    "speak": st.session_state.speech_to_play
}

voice_result = voice_component(
    key="jarvis_voice",
    data=component_data,
    default={
        "audio": None,
        "error": None
    }
)


# =========================
# RECEIVE AUDIO
# =========================

audio_data = getattr(
    voice_result,
    "audio",
    None
)

if audio_data:

    # Prevent processing the same audio twice
    st.session_state.voice_active = True

    spoken_text = transcribe_audio(
        audio_data
    )

    if spoken_text:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": spoken_text
            }
        )

        answer = ask_jarvis(
            spoken_text
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.session_state.speech_to_play = answer

        st.rerun()


# =========================
# ERROR
# =========================

component_error = getattr(
    voice_result,
    "error",
    None
)

if component_error:

    st.error(
        f"Microphone error: {component_error}"
    )


# =========================
# STATUS
# =========================

if st.session_state.voice_active:

    st.markdown(
        '<div class="voice-status">VOICE SYSTEM ACTIVE • LISTENING</div>',
        unsafe_allow_html=True
    )

else:

    st.markdown(
        '<div class="voice-status">PRESS ACTIVATE TO START</div>',
        unsafe_allow_html=True
    )


# =========================
# CLEAR SPEECH FLAG
# =========================

if st.session_state.speech_to_play:

    st.session_state.speech_to_play = ""


st.markdown(
    '<div class="voice-status">GROQ • HANDS-FREE VOICE • MULTILINGUAL</div>',
    unsafe_allow_html=True
)
