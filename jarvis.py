import streamlit as st
from groq import Groq
import datetime
import base64

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

    // Force load voices
    if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
    }

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

                const blob = new Blob(chunks, { type: "audio/webm" });

                if (blob.size < 1000) {
                    setTimeout(startListening, 300);
                    return;
                }

                const buffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(buffer);
                let binary = "";
                const chunkSize = 8192;

                for (let i = 0; i < bytes.length; i += chunkSize) {
                    const chunk = bytes.subarray(i, Math.min(i + chunkSize, bytes.length));
                    binary += String.fromCharCode(...chunk);
                }

                const base64 = btoa(binary);
                setTriggerValue("audio", base64);
            };

            recorder.start();
            listening = true;
            speechStarted = false;
            silenceStart = null;
            speechStartTime = null;

            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);

            const dataArray = new Uint8Array(analyser.fftSize);

            function detectSpeech() {
                if (!listening) return;

                analyser.getByteTimeDomainData(dataArray);
                let sum = 0;

                for (let i = 0; i < dataArray.length; i++) {
                    const value = (dataArray[i] - 128) / 128;
                    sum += value * value;
                }

                const rms = Math.sqrt(sum / dataArray.length);
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

                    const speechDuration = now - speechStartTime;
                    const silenceDuration = now - silenceStart;

                    if (speechDuration >= MIN_SPEECH_TIME && silenceDuration >= SILENCE_TIME) {
                        if (recorder && recorder.state === "recording") {
                            recorder.stop();
                        }
                        return;
                    }
                }

                animationFrame = requestAnimationFrame(detectSpeech);
            }

            detectSpeech();
        } catch (error) {
            setTriggerValue("error", String(error));
        }
    }

    // =========================
    // SPEAK RESPONSE (Jarvis-like)
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

        const utterance = new SpeechSynthesisUtterance(text);

        // Try to pick a more Jarvis-like voice
        const voices = window.speechSynthesis.getVoices();

        const preferred = [
            "Google UK English Male",
            "Microsoft George - English (United Kingdom)",
            "Microsoft David - English (United States)",
            "Daniel",
            "Alex",
            "Google US English"
        ];

        let selectedVoice = null;

        for (const name of preferred) {
            selectedVoice = voices.find(v => v.name.includes(name));
            if (selectedVoice) break;
        }

        // Fallback: any British English male voice
        if (!selectedVoice) {
            selectedVoice = voices.find(v =>
                v.lang.startsWith("en-GB") && v.name.toLowerCase().includes("male")
            );
        }

        // Final fallback: any English voice
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith("en"));
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        // Jarvis-like settings
        utterance.rate = 0.92;      // slightly slower / more measured
        utterance.pitch = 0.85;     // slightly deeper
        utterance.volume = 1.0;

        utterance.onend = () => {
            speaking = false;
            setTimeout(startListening, 250);
        };

        utterance.onerror = () => {
            speaking = false;
            setTimeout(startListening, 250);
        };

        window.speechSynthesis.speak(utterance);
    }

    // =========================
    // PYTHON → JAVASCRIPT
    // =========================
    if (data && data.speak && data.speak !== lastSpeech) {
        lastSpeech = data.speak;
        speak(data.speak);
    }

    // =========================
    // START WHEN ACTIVATED
    // =========================
    if (data && data.active === true && !listening && !speaking) {
        setTimeout(startListening, 100);
    }

    // =========================
    // CLEANUP
    // =========================
    return () => {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
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
Current date: {current_date}
Current time: {current_time}

The user is speaking to you through a voice interface.
Speak naturally and conversationally.
Reply in the same language the user uses.
Keep responses reasonably concise because your response will be spoken aloud.
Do not use markdown.
Do not use bullet points unless absolutely necessary.
Do not describe your response as text.
Never claim you performed a computer action unless the application actually performed it.
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages[-12:])
    messages.append({"role": "user", "content": user_text})

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
        audio_bytes = base64.b64decode(base64_audio)
        result = client.audio.transcriptions.create(
            file=("voice.webm", audio_bytes),
            model="whisper-large-v3-turbo",
            response_format="json"
        )
        return result.text.strip()
    except Exception as e:
        st.error(f"Voice recognition error: {e}")
        return None

# =========================
# HEADER
# =========================
st.markdown("### J.A.R.V.I.S.")
st.caption("PERSONAL AI SYSTEM")

# =========================
# CONTROLS
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("◉ ACTIVATE", use_container_width=True):
        st.session_state.voice_active = True
        st.rerun()

with col2:
    if st.button("TIME", use_container_width=True):
        answer = f"The current time is {current_time}."
        st.session_state.messages.append({"role": "user", "content": "What time is it?"})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.speech_to_play = answer
        st.rerun()

with col3:
    if st.button("CLEAR", use_container_width=True):
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
    on_audio_change=lambda: None,
    on_error_change=lambda: None,
)

# =========================
# RECEIVE AUDIO
# =========================
audio_data = getattr(voice_result, "audio", None)

if audio_data:
    st.session_state.voice_active = True
    spoken_text = transcribe_audio(audio_data)

    if spoken_text:
        st.session_state.messages.append({"role": "user", "content": spoken_text})
        answer = ask_jarvis(spoken_text)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.speech_to_play = answer
        st.rerun()

# =========================
# ERROR
# =========================
component_error = getattr(voice_result, "error", None)
if component_error:
    st.error(f"Microphone error: {component_error}")

# =========================
# STATUS
# =========================
if st.session_state.voice_active:
    st.success("VOICE SYSTEM ACTIVE • LISTENING")
else:
    st.info("PRESS ACTIVATE TO START")

# =========================
# CLEAR SPEECH FLAG
# =========================
if st.session_state.speech_to_play:
    st.session_state.speech_to_play = ""

st.caption("GROQ • HANDS-FREE VOICE • MULTILINGUAL")
