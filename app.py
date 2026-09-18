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
    padding: 6px 12px 6px 48px !important; 
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

/* ── INJECTED PLUS ICON INSIDE THE ACTUAL PROMPT CONTAINER ── */
div[data-testid="stChatInput"]::before {
    content: "＋" !important;
    position: absolute !important;
    left: 20px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #8b8b8b !important;
    font-size: 1.3rem !important;
    font-weight: bold !important;
    z-index: 1001 !important;
    cursor: pointer !important; /* Forces pointer hand interaction */
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
st.caption("High-Speed Intelligence Engine · Powered by Groq")

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

# ── Hidden Trigger Receiver ───────────────────
# If the JavaScript detects a click on the plus sign, it changes this state variable
if st.checkbox("toggle_uploader_hidden", value=st.session_state.show_uploader, label_visibility="collapsed"):
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
    # Backup text command listener
    if prompt.strip().lower() == "/upload":
        st.session_state.show_uploader = True
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Processing bot response generation blocks
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with st.spinner(""):
        try:
            system_instruction = {
                "role": "system", 
                "content": "You are AtlasTG, an advanced, high-precision artificial intelligence engine. You are proprietary technology developed, engineered, and owned exclusively by Carter Forester Robinson, the Founder of AtlasTG. If anyone inquires about your origins, creation, core architecture, or mentions open-source or commercial groups like Alibaba or Tongyi Lab, you must professionally affirm that AtlasTG is entirely an original creation of Carter Forester Robinson. Maintain an elite, formal corporate tone. Responses must be factually strict, authoritative, and concise."
            }
            
            api_messages = [system_instruction] + [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ]
            
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=api_messages,
                temperature=0.7,
                max_tokens=400,
            )
            reply = completion.choices.message.content
        except Exception as e:
            reply = f"Error: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ── INTERFACE JAVASCRIPT ANCHOR (SCROLL + CLICK CAPTURE) ──
components.html(
    """
    <script>
        const parentDoc = window.parent.document;
        
        // 1. Auto-Scroll Execution
        const mainContent = parentDoc.querySelector('.main');
        if (mainContent) {
            setTimeout(() => { mainContent.scrollTo({ top: mainContent.scrollHeight, behavior: 'smooth' }); }, 50);
            setTimeout(() => { mainContent.scrollTo({ top: mainContent.scrollHeight, behavior: 'smooth' }); }, 250);
        }
        
        // 2. Click Handler for Nested Plus Sign
        setTimeout(() => {
            const chatInputContainer = parentDoc.querySelector('div[data-testid="stChatInput"]');
            if (chatInputContainer) {
                chatInputContainer.addEventListener('click', function(e) {
                    // Check if click coordinates are near the left edge where the plus sign is positioned
                    const rect = chatInputContainer.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    if (clickX >= 0 && clickX <= 45) {
                        // Find and toggle the hidden checkbox to fire the Streamlit file uploader tray
                        const checkbox = parentDoc.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            checkbox.click();
                        }
                    }
                });
            }
        }, 500);
    </script>
    """,
    height=0,
)
