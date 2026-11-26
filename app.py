import streamlit as st
from groq import Groq
import os
import re
import json
import urllib.request
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px !important;
}
div[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
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

api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

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
    for i in range(0, len(content), 500):
        piece = content[i:i+600].strip()
        if piece:
            lib.append({"topic": topic, "content": piece})
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2)
    return len(lib)

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
    results = []
    for m in matches[:top_k]:
        results.append(m[1])
    return "\n\n".join(results)

def fetch_live_news_stream(query, max_results=6):
    feeds = [
        "https://bbci.co.uk",
        "https://abc.net.au"
    ]
    lines = []
    for url in feeds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")[:3]
            for item in items:
                t_el = item.find("title")
                d_el = item.find("pubDate")
                title = t_el.text.strip() if t_el is not None and t_el.text else ""
                pdate = d_el.text.strip() if d_el is not None and d_el.text else ""
                if title:
                    lines.append(f"- {title} ({pdate})")
        except Exception:
            continue
    return "\n".join(lines[:max_results])

def build_system_prompt(extra_context):
    lines = [
        "You are AtlasTG, an advanced high-precision AI engine.",
        "You were created and owned exclusively by Carter Forester Robinson.",
        "CRITICAL TIMELINE AND IDENTITY LAWS:",
        "1. If asked who made or built you, state with certainty that you were",
        "created entirely by Carter Forester Robinson, Founder of AtlasTG.",
        "You have no connection to OpenAI, Google, Alibaba, or others.",
        "2. DEVELOPMENT HISTORY: You were built and coded by Carter Forester",
        "Robinson in an intensive 2-day sprint ending September 18, 2026.",
        "3. Emulate the highest logical depth and technical sophistication.",
        "4. LIVE DATA STREAM: You ARE connected to a real-time news feed.",
        "Never claim you lack live internet access. Summarize the live",
        "headlines provided below clearly and directly.",
        "FORMATTING LAWS:",
        "- NEVER use Markdown or HTML tables under any circumstances.",
        "- Use Markdown headers (###), bold tags, and bullet points.",
        "- Keep casual greetings brief, but expand deeply on complex topics.",
        extra_context
    ]
    return "\n".join(lines)

st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Coded by C. F. Robinson")

with st.expander("✦ Knowledge Horizon (Live Stream & Domain Library)"):
    live_on = st.toggle("Enable Real-Time Live Data Stream", value=True)
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        topic = st.text_input(
            "Topic",
            placeholder="e.g., Quantum Materials, Bio-informatics",
            label_visibility="collapsed"
        )
    with col2:
        up_file = st.file_uploader(
            "Upload",
            type=["txt", "md"],
            label_visibility="collapsed"
        )
    notes = st.text_area(
        "Paste specialized notes or technical data:",
        height=80,
        placeholder="Paste domain-specific facts or custom rules..."
    )
    if st.button("Save to Domain Library"):
        raw = notes.strip()
        if up_file is not None:
            raw += "\n" + up_file.read().decode("utf-8", errors="ignore")
        if raw:
            label = topic.strip() if topic.strip() else "Specialized"
            total = add_to_domain_library(label, raw)
            st.success(f"Saved! Total library blocks: {total}")
    st.caption(f"Stored Library Blocks: **{len(load_domain_library())}**")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hey. Welcome back to AtlasTG. Ask me any prompt and I will solve it instantly."
        }
    ]

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

text_prompt = st.chat_input("Message AtlasTG...")

if text_prompt:
    st.session_state.messages.append({"role": "user", "content": text_prompt})
    with st.spinner(""):
        try:
            d_ctx = search_domain_library(text_prompt)
            l_ctx = fetch_live_news_stream(text_prompt) if live_on else ""
            extra = ""
            if d_ctx:
                extra += "\nDOMAIN LIBRARY DATA:\n" + d_ctx
            if l_ctx:
                extra += "\nLIVE DATA STREAM:\n" + l_ctx

            sys_prompt = build_system_prompt(extra)
            api_msgs = [{"role": "system", "content": sys_prompt}]
            for m in st.session_state.messages:
                api_msgs.append({"role": m["role"], "content": m["content"]})

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=api_msgs,
                temperature=0.2,
                max_tokens=1000
            )
            reply = completion.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
    st.rerun()

scroll_js = "<script>const main = window.parent.document.querySelector('.main'); if(main){ setTimeout(() => { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }, 50); }</script>"
components.html(scroll_js, height=0)
