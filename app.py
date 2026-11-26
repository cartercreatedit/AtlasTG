import streamlit as st
from groq import Groq
import os
import json
import re
import math
import datetime
import base64
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AtlasTG",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── ORIGINAL BORDERLESS GOOGLE-STYLE STYLING + CLEAN EXPANDER ──────
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

/* Sidebar dark styling */
section[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #222222 !important;
}

/* Clean Reasoning Expander */
div[data-testid="stExpander"] {
    background-color: #121212 !important;
    border: 1px solid #242424 !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
}
div[data-testid="stExpander"] summary {
    color: #9ca3af !important;
    font-size: 13.5px !important;
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

# ── API Key Configuration ───────────────────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)
sentiment_analyzer = SentimentIntensityAnalyzer()

# ── 1. SELF-OPTIMIZING KNOWLEDGE BASE ENGINE ────────────────────────
KB_FILE = "atlastg_knowledge.json"

def load_kb():
    if os.path.exists(KB_FILE):
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_kb(entries):
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

def ingest_text_to_kb(source_name, raw_text):
    kb = load_kb()
    # Split text into ~500-character overlapping chunks for fast retrieval
    chunks = [raw_text[i:i+500].strip() for i in range(0, len(raw_text), 400) if raw_text[i:i+500].strip()]
    for chunk in chunks:
        kb.append({
            "source": source_name,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "content": chunk
        })
    save_kb(kb)
    return len(chunks)

def ingest_url_to_kb(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        clean_text = " ".join(soup.get_text(separator=" ").split())
        return ingest_text_to_kb(url, clean_text)
    except Exception as e:
        return f"Error: {e}"

def retrieve_relevant_knowledge(query, top_k=3):
    kb = load_kb()
    if not kb:
        return ""
    query_words = set(re.findall(r'\w+', query.lower()))
    scored = []
    for item in kb:
        item_words = set(re.findall(r'\w+', item["content"].lower()))
        overlap = len(query_words.intersection(item_words))
        if overlap > 0:
            scored.append((overlap, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_items = [f"[{item['source']}]: {item['content']}" for _, item in scored[:top_k]]
    return "\n\n".join(top_items)

# ── 2. SECURE SANDBOXED PLUG-IN ARCHITECTURE ────────────────────────
def safe_calculator(expression: str) -> str:
    """Safely evaluates mathematical expressions without eval() vulnerabilities."""
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round})
    try:
        code = compile(expression, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise NameError(f"Use of '{name}' is restricted in sandbox.")
        return str(eval(code, {"__builtins__": {}}, allowed_names))
    except Exception as e:
        return f"Calculation error: {e}"

def get_current_time() -> str:
    return datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

def self_update_memory(fact: str) -> str:
    ingest_text_to_kb("AtlasTG Autonomous Memory", fact)
    return f"Successfully committed to permanent knowledge base: '{fact}'"

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "safe_calculator",
            "description": "Evaluates mathematical equations, algebra, or scientific calculations safely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression, e.g., 'sqrt(144) * 3.14'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the exact current system date and time.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "self_update_memory",
            "description": "Saves a verified fact, user preference, or new technical standard into AtlasTG's permanent knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The verified fact or rule to remember permanently."}
                },
                "required": ["fact"]
            }
        }
    }
]

def execute_tool_call(tool_call):
    fn_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")
    if fn_name == "safe_calculator":
        return safe_calculator(args.get("expression", ""))
    elif fn_name == "get_current_time":
        return get_current_time()
    elif fn_name == "self_update_memory":
        return self_update_memory(args.get("fact", ""))
    return "Unknown tool."

# ── 3. ADVANCED EMOTIONAL MODELING ──────────────────────────────────
def analyze_emotional_context(text):
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound <= -0.4:
        return "User sentiment is distressed, frustrated, or negative. Respond with heightened empathy, patience, and supportive clarity while maintaining logical rigor."
    elif compound >= 0.5:
        return "User sentiment is enthusiastic or positive. Match their constructive energy with sharp, encouraging precision."
    return "User sentiment is neutral or analytical. Maintain calm, high-precision executive clarity."

# ── SIDEBAR: KNOWLEDGE BASE & MULTIMODAL CONTROLS ───────────────────
with st.sidebar:
    st.markdown("### ✦ AtlasTG Core Modules")
    
    # Knowledge Base Ingestion
    st.markdown("**Knowledge Base Ingestion**")
    url_input = st.text_input("Ingest Live Website URL", placeholder="https://...")
    if st.button("Learn URL") and url_input:
        with st.spinner("Ingesting web data..."):
            res = ingest_url_to_kb(url_input)
            if isinstance(res, int):
                st.success(f"Indexed {res} knowledge chunks.")
            else:
                st.error(res)

    uploaded_doc = st.file_uploader("Upload Knowledge File (.txt, .md)", type=["txt", "md"])
    if uploaded_doc and st.button("Index Document"):
        text_data = uploaded_doc.read().decode("utf-8", errors="ignore")
        chunks_added = ingest_text_to_kb(uploaded_doc.name, text_data)
        st.success(f"Indexed {chunks_added} chunks from {uploaded_doc.name}.")

    kb_count = len(load_kb())
    st.caption(f"Active Memory Nodes: **{kb_count}**")

    st.divider()
    # Multimodal Vision Input
    st.markdown("**Multimodal Vision Input**")
    uploaded_image = st.file_uploader("Attach Image for Analysis", type=["png", "jpg", "jpeg", "webp"])

# ── Header ──────────────────────────────────────────────────────────
st.markdown("<h1>AtlasTG</h1>", unsafe_allow_html=True)
st.caption("High-Speed Intelligence Engine · Coded by C. F. Robinson")

# ── Session state ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
