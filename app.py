import streamlit as st
from groq import Groq
import os
import streamlit.components.v1 as components
import uuid

# ── 1. GLOBAL LAYOUT CONFIGURATION ─────────────────────────
st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── 2. GOOGLE AI STYLE MIDNIGHT THEME CUSTOMIZATION ─────────────────────────
st.markdown("""
<style>
.stApp { 
    background-color: #0d0d0d; 
    color: #e3e3e3; 
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
    font-weight: 400 !important; 
    font-size: 1.8rem !important;
    font-family: 'Google Sans', Arial, sans-serif;
}
.stCaption { 
    color: #9e9e9e !important; 
}
/* Clear standard spacing anomalies */
div[data-testid="stChatMessage"] { 
    background-color: transparent !important; 
    border: none !important; 
    box-shadow: none !important; 
    padding: 0px !important; 
}
div[data-testid="stMarkdownContainer"] p { 
    color: #e3e3e3 !important; 
    font-size: 15.5px !important; 
    line-height: 1.6 !important; 
}
/* User Message Pointed Bubbles */
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) { 
    display: flex !important; 
    justify-content: flex-end !important; 
    margin: 16px 0 !important; 
}
div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) > div:nth-child(2) { 
    background-color: #1e1e1e !important; 
    border: 1px solid #2d2d2d !important; 
    padding: 12px 18px !important; 
    border-radius: 18px !important; 
    border-top-right-radius: 2px !important; 
    max-width: 80% !important; 
    display: inline-block !important; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important; 
}
/* Assistant Message Layout */
div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) { 
    display: flex !important; 
    justify-content: flex-start !important; 
    margin: 16px 0 !important; 
}
div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) > div:nth-child(2) { 
    background-color: transparent !important; 
    border: none !important; 
    padding: 4px 0px !important; 
    box-shadow: none !important; 
    max-width: 100% !important; 
}
/* Google Console Style Dock Fixed Chat Input */
div[data-testid="stChatInput"] { 
    position: fixed !important; 
    bottom: 32px !important; 
    left: 50% !important; 
    transform: translateX(-50%) !important; 
    width: min(760px, 92vw) !important; 
    z-index: 999 !important; 
}
.stChatInput { 
    background-color: #1e1e1e !important; 
    border: 1px solid #2d2d2d !important; 
    border-radius: 28px !important; 
    box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important; 
    padding: 6px 12px 6px 20px !important; 
}
.stChatInput:focus-within { 
    border: 1px solid #444444 !important; 
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important; 
    outline: none !important; 
}
div[data-testid="stChatInput"] *, .stChatInput div[data-baseweb="textarea"], .stChatInput div[data-baseweb="base-input"], .stChatInput textarea { 
    border: none !important; 
    background-color: transparent !important; 
    box-shadow: none !important; 
    outline: none !important; 
}
.stChatInput textarea { 
    color: #f5f5f5 !important; 
    font-size: 15.5px !important; 
}

/* ── GOOGLE-STYLE SIDEBAR DIRECTORY PANEL ── */
section[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #1f1f1f !important;
}
section[data-testid="stSidebar"] h3 {
    color: #c4c7c5 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 20px 0 10px 0;
}
/* New Chat + Accent Button styling */
div.stButton > button {
    border-radius: 24px !important;
}
</style>
""", unsafe_allow_html=True)

# ── 3. API CONFIGURATION & CORE VALIDATION ─────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY environment variable.")
    st.stop()

client = Groq(api_key=api_key)

# ── 4. MULTI-CHAT INTERACTIVE HISTORY INITIALIZATION ─────────────────────
# Initialize global conversation memory map if missing
if "all_chats" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.all_chats = {
        initial_id: {
            "title": "Welcome to AtlasTG",
            "messages": [{"role": "assistant", "content": "Hey. Welcome back to AtlasTG. Ask me any prompt and I will solve it instantly."}]
        }
    }
    st.session_state.current_chat_id = initial_id

# Safe pointers to current chat active parameters
current_id = st.session_state.current_chat_id
active_chat = st.session_state.all_chats[current_id]

# ── 5. SIDEBAR WORKSPACE ARCHIVE PANEL (GOOGLE AI STYLE) ─────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    # New Chat initialization command trigger
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {
            "title": "New Chat Thread",
            "messages": [{"role": "assistant", "content": "Hey. Welcome back to AtlasTG. Ask me any prompt and I will solve it instantly."}]
        }
        st.session_state.current_chat_id = new_id
        st.rerun()
        
    st.markdown("### Recent Chats")
    
    # Render interactive log for all saved chat tracking sessions
    for chat_id, data in list(st.session_state.all_chats.items()):
        # Styling marker to highlight the active chosen context matrix thread
        button_label = f"💬 {data['title'][:24]}..." if len(data['title']) > 24 else f"💬 {data['title']}"
        if chat_id == st.session_state.current_chat_id:
            button_label = f"👉 {data['title'][:22]}"
            
        if st.button(button_label, key=f"nav_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.rerun()

# ── 6. MAIN WORKSPACE DISPLAY HEADER ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Coded by C. F. Robinson")

# ── 7. TIMELINE PIPELINE GENERATION ──────────────────
for msg in active_chat["messages"]:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                <div style="background-color: #1e1e1e; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                    {msg["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── 8. LIVE USER CONSOLE INPUT DOCK ─────────────────────
text_prompt = st.chat_input("Message AtlasTG...")

# ── 9. ADVANCED COMPILATION HANDLING ENGINE ──────────────────────
if text_prompt:
    active_chat["messages"].append({"role": "user", "content": text_prompt})
    
    # Dynamically update sidebar thread title using the first user question
    if active_chat["title"] == "New Chat Thread" or active_chat["title"] == "Welcome to AtlasTG":
        active_chat["title"] = text_prompt[:30]
        
    st.rerun()

# Run the core api processing loop if last element is user text prompt array matrix
if len(active_chat["messages"]) > 0 and active_chat["messages"][-1]["role"] == "user":
    sys_content = (
        "You are AtlasTG, an advanced, high-precision artificial intelligence engine. "
        "You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. "
        "CRITICAL TIMELINE AND IDENTITY LAWS:\n"
        "1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation.\n"
        "2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix.\n"
        "3. Your conversational style emulates the highest standards of logical depth, emotional clarity, and technical sophistication.\n"
        "FORMATTING LAWS:\n"
        "- NEVER use Markdown or HTML tables under any circumstances.\n"
        "- Structure information visually using Markdown headers (###), bold tags, and bullet points.\n"
        "- Dynamically scale response lengths. Keep greetings or casual phrases concise, but expand deeply into structured paragraphs for complex logic, emotional scenarios, or relationship questions."
    )
    
    api_messages = [{"role": "system", "content": sys_content}] + [{"role": m["role"], "content": m["content"]} for m in active_chat["messages"]]
    
    completion = client.chat.completions.create(model="openai/gpt-oss-120b", messages=api_messages, temperature=0.2, max_tokens=1000)
    reply = completion.choices.message.content
        
    active_chat["messages"].append({"role": "assistant", "content": reply})
    st.rerun()

