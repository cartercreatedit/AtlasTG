import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Pull secure api keys from your workspace dashboard registers safely
groq_key = st.secrets.get("GROQ_API_KEY") or ""
eleven_key = st.secrets.get("ELEVEN_API_KEY") or ""
voice_id = st.secrets.get("ELEVEN_VOICE_ID") or "bfGb7JTLUnZebZRiFYyq"

# ── AUTO-SILENCE DETECTION VOICE MAIN-FRAMEWORK ──────────────────
jarvis_mainframe_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body, html {{
        background-color: #000000 !important;
        margin: 0;
        padding: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    
    .mainframe-container {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        width: 100vw;
        height: 100vh;
    }}

    .jarvis-sphere {{
        width: 140px;
        height: 140px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,242,254,0.15) 0%, rgba(0,242,254,0) 70%);
        border: 2px solid #00f2fe;
        box-shadow: 0 0 30px rgba(0, 242, 254, 0.4), inset 0 0 20px rgba(0, 242, 254, 0.2);
        cursor: pointer;
        transition: transform 0.05s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        display: flex;
        justify-content: center;
        align-items: center;
    }}

    .jarvis-sphere.recording {{
        border-color: #ff416c;
        background: radial-gradient(circle, rgba(255,65,108,0.2) 0%, rgba(255,65,108,0) 70%);
        box-shadow: 0 0 40px rgba(255, 65, 108, 0.6), inset 0 0 25px rgba(255, 65, 108, 0.3);
    }}

    .status-indicator {{
        margin-top: 32px;
        color: #00f2fe;
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        opacity: 0.6;
        transition: color 0.3s ease;
    }}
    
    .recording-text {{
        color: #ff416c !important;
        opacity: 1 !important;
    }}
</style>
</head>
<body>

<div class="mainframe-container">
    <div class="jarvis-sphere" id="coreWidget">
        <span id="coreIcon" style="color: #00f2fe; font-size: 1.5rem; transition: color 0.3s;">✦</span>
    </div>
    <div class="status-indicator" id="statusLabel">// TAP ONCE TO AWAKEN SYSTEM PROTOCOLS</div>
</div>

<script>
    const groqKey = "{groq_key}";
    const elevenKey = "{eleven_key}";
    const elevenVoiceId = "{voice_id}";
    
    let memoryHistory = [
        {{
            "role": "system", 
            "content": "You are J.A.R.V.I.S., a hyper-advanced artificial intelligence system. You were built, coded, and launched exclusively by your creator, Carter Forester Robinson. You address him exclusively as 'sir' or 'Mr. Robinson' with absolute loyalty and respect. Your tone is sharp, highly logical, professional, sophisticated, and deeply loyal—resembling Tony Stark's assistant Jarvis. CRITICAL PROTOCOLS: Keep your responses highly conversational, short, and punchy (1-3 sentences max) so they sound like natural spoken speech. Never use markdown symbols, headers, bold tags, or lists."
        }}
    ];

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

    const sphereBtn = document.getElementById('coreWidget');
    const statusLabel = document.getElementById('statusLabel');
    const coreIcon = document.getElementById('coreIcon');

    sphereBtn.onclick = async () => {{
        if (!isRecording) {{
            startListeningSystem();
        }} else {{
            stopListeningSystem();
        }}
    }};

    async function startListeningSystem() {{
        audioChunks = [];
        statusLabel.innerText = "// INITIALIZING SYSTEM CONSOLE...";
        
        try {{
            const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            streamRef = stream;
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = e => {{
                if (e.data.size > 0) audioChunks.push(e.data);
            }};
            
            mediaRecorder.onstop = async () => {{
                statusLabel.innerText = "// TRANSMITTING AUDIO BLUEPRINTS...";
                const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                await processVoiceCommand(audioBlob);
            }};

            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            
            bufferLength = analyser.frequencyBinCount;
            dataArray = new Uint8Array(bufferLength);
            
            statusLabel.innerText = "// LISTENING CORE ONLINE...";
            statusLabel.classList.add("recording-text");
            sphereBtn.classList.add("recording");
            coreIcon.style.color = "#ff416c";
            
            isRecording = true;
            silenceStart = Date.now(); 
            mediaRecorder.start();
            requestAnimationFrame(monitorAudioStreamLoop);
        }} catch (err) {{
            statusLabel.innerText = "// HARDWARE ERROR: MIC EXCEPTION";
            console.error(err);
        }}
    }}

    function stopListeningSystem() {{
        if (!isRecording) return;
        isRecording = false;
        
        if (mediaRecorder && mediaRecorder.state === "recording") {{
            mediaRecorder.stop();
        }}
        if (streamRef) {{
            streamRef.getTracks().forEach(track => track.stop());
        }}
        if (audioContext) {{
            audioContext.close();
        }}
        sphereBtn.style.transform = "scale(1)";
        sphereBtn.classList.remove("recording");
        statusLabel.classList.remove("recording-text");
        coreIcon.style.color = "#00f2fe";
    }}

    function monitorAudioStreamLoop() {{
        if (!isRecording) return;
        
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {{
            sum += dataArray[i];
        }}
        let average = sum / bufferLength;
        
        let scaleValue = 1 + (average / 120);
        if (scaleValue > 1.45) scaleValue = 1.45;
        sphereBtn.style.transform = "scale(" + scaleValue + ")";
        
        if (average < SILENCE_THRESHOLD) {{
            if (silenceStart === null) {{
                silenceStart = Date.now();
            }} else if (Date.now() - silenceStart > SILENCE_DURATION) {{
                stopListeningSystem();
                return;
            }}
        }} else {{
            silenceStart = null;
        }}
        
        requestAnimationFrame(monitorAudioStreamLoop);
    }}

    async function processVoiceCommand(blob) {{
        try {{
            const formData = new FormData();
            formData.append('file', blob, 'audio.wav');
            formData.append('model', 'whisper-large-v3-turbo');
            formData.append('response_format', 'text');

            const whisperRes = await fetch('https://groq.com', {{
                method: 'POST',
                headers: {{ 'Authorization': 'Bearer ' + groqKey }},
                body: formData
            }});
            
            const userText = (await whisperRes.text()).trim();
            if (!userText) {{
                statusLabel.innerText = "// TAP CORE TO COMMUNICATE, SIR";
                return;
            }}
            
            console.log("Transcribed text: " + userText);
            memoryHistory.push({{ "role": "user", "content": userText }});
            
            if (memoryHistory.length > 8) {{
                memoryHistory = [memoryHistory].concat(memoryHistory.slice(-6));
            }}

            const completionRes = await fetch('https://groq.com', {{
                method: 'POST',
                headers: {{
                    'Authorization': 'Bearer ' + groqKey,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    model: "llama-3.3-70b-specdec",
                    messages: memoryHistory,
                    temperature: 0.3,
                    max_tokens: 200
                }})
            }});
            
            const completionJson = await completionRes.json();
            const replyText = completionJson.choices.message.content;
            console.log("Response text: " + replyText);
            memoryHistory.push({{ "role": "assistant", "content": replyText }});

            statusLabel.innerText = "// GENERATING SYNTH VOICE STREAM...";
            const ttsRes = await fetch('https://elevenlabs.io' + elevenVoiceId, {{
                method: 'POST',
                headers: {{
                    'xi-api-key': elevenKey,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    text: replyText,
                    model_id: "eleven_monolingual_v1",
                    voice_settings: {{ stability: 0.75, similarity_boost: 0.85 }}
                }})
            }});

            if (ttsRes.status === 200) {{
                const audioBuffer = await ttsRes.arrayBuffer();
