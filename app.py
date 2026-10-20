import streamlit as st
from groq import Groq
import os
import streamlit.components.v1 as components
import sqlite3
import hashlib
import uuid
import json

# ── 1. GLOBAL LAYOUT CONFIGURATION ─────────────────────────
st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── 2. DATABASE PERSISTENCE FRAMEWORK MATRIX ────────────────
DB_FILE = "atlastg_matrix.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats 
                 (chat_id TEXT PRIMARY KEY, username TEXT, title TEXT, messages_json TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (username.strip().lower(),))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False

def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username.strip().lower(), hash_password(password)))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def load_user_chats(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT chat_id, title, messages_json FROM chats WHERE username=?", (username.strip().lower(),))
    rows = c.fetchall()
    conn.close()
    
    chats = {}
    for r in rows:
        chats[r[0]] = {
            "title": r[1],
            "messages": json.loads(r[2])
        }
    return chats

def save_or_update_chat(chat_id, username, title, messages):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    messages_json = json.dumps(messages)
    c.execute('''INSERT INTO chats (chat_id, username, title, messages_json) 
                 VALUES (?, ?, ?, ?)
                 ON CONFLICT(chat_id) DO UPDATE SET 
                 title=excluded.title, messages_json=excluded.messages_json''', 
              (chat_id, username.strip().lower(), title, messages_json))
    conn.commit()
    conn.close()

# Initialize database tracking files natively
init_db()

# ── 3. GOOGLE AI STYLE MIDNIGHT THEME CUSTOMIZATION ─────────────────────────
st.markdown("""
<style>
.stApp { 
    background-color: #0d0d0d; 
    color: #e3e3e3; 
}
.main .block-container { 
    padding-top: 4rem; 
    padding-bottom: 160px !important; 
    max-width: 760px; 
    min-height: 100vh; 
}
#MainMenu, footer, .stDeployButton { 
    visibility: hidden; 
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
header[data-testid="stHeader"] button {
    color: #ffffff !important;
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
div.stButton > button {
    border-radius: 24px !important;
}
.auth-container {
    background-color: #111111;
    border: 1px solid #222222;
    border-radius: 16px;
    padding: 30px;
    max-width: 420px;
    margin: 80px auto 0 auto;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
</style>
""", unsafe_allow_html=True)

# ── 4. API CONFIGURATION & CORE VALIDATION ─────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY environment variable.")
    st.stop()

client = Groq(api_key=api_key)

# ── 5. AUTHENTICATION CONTROLLER SYSTEM ────────────────────────────────────
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 5px;'>AtlasTG Engine</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-size: 13px;'>Secure Core Verification Gate</p>", unsafe_allow_html=True)
    
    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
    
    with tab_login:
        login_user = st.text_input("Username", key="login_username")
        login_pass = st.text_input("Password", type="password", key="login_password")
        if st.button("Access Engine Pipeline", use_container_width=True):
            if verify_user(login_user, login_pass):
                st.session_state.logged_in_user = login_user.strip().lower()
                st.rerun()
            else:
                st.error("Invalid credentials footprint.")
                
    with tab_signup:
        reg_user = st.text_input("Choose Username", key="reg_username")
        reg_pass = st.text_input("Choose Password", type="password", key="reg_password")
        if st.button("Register Identity Frame", use_container_width=True):
            if reg_user.strip() == "" or reg_pass.strip() == "":
                st.error("Fields cannot stand empty.")
            elif register_user(reg_user, reg_pass):
                st.success("Identity locked! Switching to authentication...")
                st.session_state.logged_in_user = reg_user.strip().lower()
                st.rerun()
            else:
                st.error("Username index footprint already occupied.")
                
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── 6. DATA CONTEXT MEMORY RECOVERY ──────────────────────────────────────────
username = st.session_state.logged_in_user

if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_user_chats(username)
    
    if not st.session_state.all_chats:
        initial_id = str(uuid.uuid4())
        st.session_state.all_chats = {
            initial_id: {
                "title": "Welcome to AtlasTG",
                "messages": [{"role": "assistant", "content": "Hey. Welcome back to AtlasTG. Ask me any prompt and I will solve it instantly."}]
            }
        }
        save_or_update_chat(initial_id, username, "Welcome to AtlasTG", st.session_state.all_chats[initial_id]["messages"])
        st.session_state.current_chat_id = initial_id
    else:
        # FIXED: Forces extraction of single string key natively to stop sequence array errors
        st.session_state.current_chat_id = list(st.session_state.all_chats.keys())[0]

current_id = st.session_state.current_chat_id
active_chat = st.session_state.all_chats[current_id]

# ── 7. GOOGLE-STYLE SIDEBAR LOGISTICS DIRECTORY ─────────────────────────────
with st.sidebar:
    st.markdown(f"<p style='color: #8b8b8b; font-size: 13px; margin-top: 10px;'>Identity: <b>{username}</b></p>", unsafe_allow_html=True)
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {
