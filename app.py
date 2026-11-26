import streamlit as st
from groq import Groq
import os
import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── ORIGINAL BORDERLESS GOOGLE-STYLE STYLING ─────────────────────────
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
#MainMenu, footer, .stDeployButton {
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

/* Subtle Knowledge Expander */
div[data-testid="stExpander"] {
    background-color: #111111 !important;
    border: 1px solid #222222 !important;
    border-radius: 14px !important;
    margin-bottom: 16px !important;
}
div[data-testid="stExpander"] summary {
    color: #8b8b8b !important;
    font-size: 13px !important;
}

/* Clear default Streamlit padding baggage */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}

/* Force clean text behavior inside all markdown elements */
div[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
}

/* ── PREMIUM BORDERLESS MIDNIGHT TEXT BOX (NO WHITE RING HIGHLIGHT) ── */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(760px, 92vw) !important;
    z-index: 999 !important;
}
.stChatInput {
    background-color: #161616 !important;
    border: none !important; 
    border-radius: 32px !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    padding: 6px 12px 6px 20px !important; 
}
.stChatInput:focus-within {
    border: none !important;
    box-shadow: 0 4px 35px rgba(0,0,0,0.6) !important;
    outline: none !important;
}

/* Obliterate inner background border constraints */
div[data-testid="stChatInput"] *,
.stChatInput div[data-baseweb="textarea"],
.stChatInput div[data-baseweb="base-input"],
.stChatInput textarea {
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
}
.stChatInput textarea {
    color: #f4f4f4 !important;
    font-size: 15.5px !important;
}
</style>
""", unsafe_allow_html=True)

# ── API Key Configuration ─────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ── 1. EXPANDED KNOWLEDGE HORIZON ENGINE ──────
KB_FILE = "atlastg_domain_library.json"

def load_domain_library():
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def add_to_domain_library(topic, content):
    lib = load_domain_library()
    chunks = [content[i:i+600].strip() for i in range(0, len(content), 500) if content[i:i+600].strip()]
    for chunk in chunks:
        lib.append({"topic": topic, "content": chunk})
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2)
    return len(chunks)

def search_domain_library(query, top_k=3):
    lib = load_domain_library()
    if not lib:
        return ""
    q_words = set(re.findall(r'\w+', query.lower()))
    matches = []
    for item in lib:
        c_words = set(re.findall(r'\w+', item["content"].lower()))
        score = len(q_words.intersection(c_words))
        if score > 0:
            matches.append((score, f"[{item['topic']}]: {item['content']}"))
    matches.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([m[1] for m in matches[:top_k]])

def fetch_live_news_stream(query, max_results=5):
    try:
        encoded_q = urllib.parse.quote(query)
        rss_url = f"https://google.com{encoded_q}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")[:max_results]
        if not items:
            return ""
        headlines = []
        for item in items:
            title = item.find("title").text if item.find("title") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            headlines.append(f"- {title} ({pub_date})")
        return "\n".join(headlines)
    except Exception:
        return ""

# ── Header ────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Coded by C. F. Robinson")

# ── Subtle Knowledge Horizon Control Bar ──────
with st.expander("✦ Knowledge Horizon (Live Stream & Domain Library)"):
    live_stream_enabled = st.toggle("Enable Real-Time Live Data Stream", value=True)
    
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        domain_topic = st.text_input("Topic / Field Name", placeholder="e.g., Quantum Materials, Bio-informatics", label_visibility="collapsed")
    with col2:
        uploaded_txt = st.file_uploader("Upload .txt", type=["txt", "md"], label_visibility="collapsed")
        
    domain_notes = st.text_area("Paste specialized notes or technical data to add to AtlasTG's library:", height=80, placeholder="Paste domain-specific facts, research notes, or custom rules here...")
    
    if st.button("Save to Domain Library"):
        raw_text = domain_notes.strip()
        if uploaded_txt is not None:
            raw_text += "\n" + uploaded_txt.read().decode("utf-8", errors="ignore")
        if raw_text:
            topic_label = domain_topic.strip() if domain_topic.strip() else "Specialized Knowledge"
            added = add_to_domain_library(topic_label, raw_text)
            st.success(f"Added {added} knowledge blocks under '{topic_label}'.")
            
    st.caption(f"Stored Domain Knowledge Blocks: **{len(load_domain_library())}**")

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey. Welcome back to AtlasTG. Ask me any prompt and I will solve it instantly."}
    ]

# ── Render Message Timeline using Native Safe Structures ──────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col_spacer, col_bubble = st.columns([0.2, 0.8])
        with col_bubble:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; width: 100%; clear: both;">
                <div style="background-color: #1a1a1a; border: 1px solid #2d2d2d; color: #e3e3e3; padding: 12px 18px; border-radius: 18px; border-top-right-radius: 2px; font-size: 15.5px; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: left; width: fit-content; max-width: 100%;">
                    {msg["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin: 16px 0; clear: both; text-align: left;">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── SINGLE TEXT INPUT CONSOLE DOCK ─────────────────────
text_prompt = st.chat_input("Message AtlasTG...")

# ── PROCESS INJECTED PARAMETERS ──────────────────────
if text_prompt:
    st.session_state.messages.append({"role": "user", "content": text_prompt})
    
    with st.spinner(""):
        try:
            domain_context = search_domain_library(text_prompt)
            live_context = fetch_live_news_stream(text_prompt) if live_stream_enabled else ""
            
            knowledge_injection = ""
            if domain_context:
                knowledge_injection += f"\n\nDOMAIN-SPECIFIC LIBRARY DATA:\n{domain_context}\n"
            if live_context:
                knowledge_injection += f"\n\nREAL-TIME LIVE DATA STREAM (LATEST HEADLINES):\n{live_context}\n"

            sys_content = (
                "You are AtlasTG, an advanced, high-precision artificial intelligence engine. "
                "You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. "
                "CRITICAL TIMELINE AND IDENTITY LAWS: "
                "1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation. "
                "2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix. "
                "3. Your conversational style emulates the highest standards of logical depth, emotional clarity, and technical sophistication. "
