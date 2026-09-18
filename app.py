import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
import io
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS Configuration ─────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 160px !important;
    max-width: 760px;
    min-height: 100vh;
}
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden;
}
h1 {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 1.75rem !important;
}
.stCaption {
    color: #8b8b8b !important;
}

/* Clear default Streamlit padding baggage */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}

/* ── EXACT STEALTH INPUT BOX MATCH (NO HIGHLIGHT OUTLINE) ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}

/* Outer frame matches Gemini sizing but with no visible border frame lines */
.stChatInput {
    background-color: #161616 !important;
    border: none !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 52px !important; /* Locks left text indentation space */
    transition: background-color 0.2s ease, box-shadow 0.2s ease !important;
}

/* Obliterated the active white glowing lines on focus state completely */
.stChatInput:focus-within {
    border: none !important;
    outline: none !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.02) !important;
}

/* OBLITERATE EVERY SINGLE HIDDEN INTERNAL BORDER AND BACKGROUND SHADOW */
div[data-testid="stChatInput"] *,
.stChatInput div[data-baseweb="textarea"],
.stChatInput div[data-baseweb="base-input"],
.stChatInput textarea {
    border: none !important;
    border-color: transparent !important;
    background-color: transparent !important;
    background: transparent !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Sizing text inside the container perfectly */
.stChatInput textarea {
    color: #f4f4f4 !important;
    font-size: 15.5px !important;
    padding: 8px 4px !important;
}

/* ── ＋ FIXED STRAIGHT INSIDE THE PROMPT BOX FRAME ── */
div[data-testid="stChatInput"]::before {
    content: "＋" !important;
    position: absolute !important;
    left: 22px !important; /* Physically anchors it to the inner left padding wall */
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #8b8b8b !important;
    font-size: 1.4rem !important;
    font-weight: bold !important;
    z-index: 1002 !important;
    cursor: pointer !important;
    pointer-events: all !important; /* Makes the embedded symbol fully clickable */
}
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ── Header ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Hybrid Intelligence Engine · Powered by Groq")

# ── Helper ────────────────────────────────────
def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. You can talk to me or upload an image and ask about it."}
    ]
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# ── Render Message Timeline using Airtight Inline Boxes ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        if isinstance(msg["content"], list):
            text_part = next((part["text"] for part in msg["content"] if part["type"] == "text"), "")
            st.markdown(
                f'''
                <div style="display: flex; justify-content: flex-end; width: 100%; margin: 16px 0; clear: both;">
                    <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; max-width: 80%; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                        {text_part}
                    </div>
                </div>
                ''', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'''
                <div style="display: flex; justify-content: flex-end; width: 100%; margin: 16px 0; clear: both;">
                    <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; max-width: 80%; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                        {msg["content"]}
                    </div>
                </div>
                ''', 
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            f'''
            <div style="display: flex; justify-content: flex-start; width: 100%; margin: 16px 0; clear: both;">
                <div style="color: #e3e3e3; padding: 4px 0px; max-width: 100%; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
                    {msg["content"]}
                </div>
            </div>
            ''', 
            unsafe_allow_html=True
        )

# ── Invisible Interceptor Variable ────────────
if st.checkbox("toggle_drawer_state", value=st.session_state.show_uploader, label_visibility="collapsed"):
    st.session_state.show_uploader = True

# ── File Upload Drawer ────────────────────────
if st.session_state.show_uploader:
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="file_uploader"
    )
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file
        st.session_state.show_uploader = False
        st.rerun()

# ── Chat input ────────────────────────────────
prompt = st.chat_input("Message AtlasTG...")

# ── Handle send ───────────────────────────────
if prompt:
    if prompt.strip().lower() == "/upload":
        st.session_state.show_uploader = True
        st.rerun()

    uploaded_file = st.session_state.uploaded_image

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        b64_image = image_to_base64(image)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
        ]
        st.session_state.uploaded_image = None
    else:
        user_content = prompt

    st.session_state.messages.append({"role": "user", "content": user_content})

    with st.chat_message("user"):
        if uploaded_file is not None:
            st.image(uploaded_file, use_container_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                system_instruction = {
                    "role": "system", 
                    "content": "You are AtlasTG, an advanced, high-precision artificial intelligence engine. You are proprietary technology developed, engineered, and owned exclusively by Carter Forester Robinson, the Founder of AtlasTG. If anyone inquires about your origins, creation, core architecture, or mentions open-source or commercial groups like Alibaba or Tongyi Lab, you must professionally affirm that AtlasTG is entirely an original creation of Carter Forester Robinson. Maintain an elite, formal corporate tone. Responses must be factually strict, authoritative, and concise."
                }
                
                api_messages = [system_instruction]
                is_multimodal = False
                
                for m in st.session_state.messages:
                    if isinstance(m["content"], list):
                        is_multimodal = True
                    api_messages.append({"role": m["role"], "content": m["content"]})
                
                if is_multimodal:
                    target_model = "llama-3.2-11b-vision-preview" 
                else:
                    target_model = "openai/gpt-oss-20b" 
                
                completion = client.chat.completions.create(
                    model=target_model,
                    messages=api_messages,
                    temperature=0.3,
                    max_tokens=400,
                )
                # FIXED EXTRACTION: Target position 0 array index to unpack response cleanly
                reply = completion.choices[0].message.content
            except Exception as e:
                reply = f"Error: {e}"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ── AUTO-SCROLL + RELIABLE INSIDE CLICK TRIGGER INTERFACE ──
