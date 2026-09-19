import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import os
import base64
import requests
import tempfile

st.set_page_config(
    page_title="J.A.R.V.I.S. Core",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background:#000 !important;
    }

    header, footer, #MainMenu {
        display:none !important;
    }

    .block-container {
        padding:0 !important;
        margin:0 !important;
        max-width:100% !important;
    }

    [data-testid="stVerticalBlock"] {
        gap:0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# API
# ============================================================

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
ELEVEN_API_KEY = st.secrets.get("ELEVEN_API_KEY", "")
ELEVEN_VOICE_ID = st.secrets.get(
    "ELEVEN_VOICE_ID",
    "bfGb7JTLUnZebZRiFYyq",
)

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., an advanced personal AI assistant. "
                "Address Carter as sir or Mr. Robinson when appropriate. "
                "Keep responses concise and natural for voice. "
                "Do not use markdown, bullet points, or unnecessary formatting."
            ),
        }
    ]

if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

if "processing" not in st.session_state:
    st.session_state.processing = False

# ============================================================
# FRONTEND FILE
# ============================================================

component_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "jarvis_component",
)

os.makedirs(component_dir, exist_ok=True)

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
    background:#000;
    overflow:hidden;
}

body {
    display:flex;
    align-items:center;
    justify-content:center;
}

.container {
    width:100%;
    height:330px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}

.sphere {
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
    box-sizing:border-box;
}

.inner {
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

.name {
    margin-top:30px;
    color:#00f2fe;
    font-family:Arial,sans-serif;
