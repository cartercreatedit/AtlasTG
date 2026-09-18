import streamlit as st
import requests

st.set_page_config(page_title="AtlasTG AI", page_icon="🐆", layout="centered")

# Custom UI Theme Layout styling
st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #0A0D14 0%, #05070B 100%) !important; color: #F8FAFC !important; }
        .app-header { text-align: center; font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) { background: rgba(30, 41, 59, 0.4) !important; border-radius: 18px 18px 4px 18px !important; margin: 12px 0 12px auto !important; max-width: 85% !important; }
        div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) { background: rgba(15, 23, 42, 0.6) !important; border-radius: 18px 18px 18px 4px !important; margin: 12px auto 12px 0px !important; max-width: 85% !important; }
        [data-testid="stChatInput"] { border-radius: 28px !important; background-color: #111827 !important; }
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">AtlasTG AI</div>', unsafe_allow_html=True)

# Connection details mapping directly to Groq's high-speed server pipeline
API_URL = "https://groq.com"

# 1. PASTE YOUR NEW COPIED GSK_ KEY DIRECTLY BETWEEN THESE QUOTES:
GROQ_KEY = "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"

# Chat Memory tracking timeline array
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are AtlasTG, a helpful AI assistant. Always keep answers very short, concise, and summary-focused. Limit responses strictly to 1 or 2 sentences max."}
    ]

# Render timeline history message rows
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Direct input processing loop
if user_input := st.chat_input("Message AtlasTG..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        response = requests.post(
            API_URL, 
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}, 
            json={"model": "llama3-8b-8192", "messages": st.session_state.messages, "max_tokens": 100, "temperature": 0.3}
        )
        
        # Raw Data Extraction Handshake
        bot_answer = response.json()['choices']['message']['content'].strip()
        st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})
