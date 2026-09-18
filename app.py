import streamlit as st
from groq import Groq

# 1. Advanced Luxury Page Config
st.set_page_config(page_title="AtlasTG AI", page_icon="🐆", layout="centered")

# 2. Hyper-Modern Obsidian CSS Injector
st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #0A0D14 0%, #05070B 100%) !important; color: #F8FAFC !important; font-family: '-apple-system', BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; }
        .app-header { text-align: center; font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 2px !important; letter-spacing: -0.8px; }
        .app-subtitle { text-align: center; color: #64748B; font-size: 14px; font-weight: 500; margin-bottom: 30px !important; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) { background: rgba(30, 41, 59, 0.4) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 18px 18px 4px 18px !important; padding: 16px 20px !important; margin: 12px 0px 12px auto !important; max-width: 85% !important; animation: fadeIn 0.4s ease forwards; }
        div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) { background: rgba(15, 23, 42, 0.6) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.02); border-radius: 18px 18px 18px 4px !important; padding: 16px 20px !important; margin: 12px auto 12px 0px !important; max-width: 85% !important; animation: fadeIn 0.4s ease forwards; }
        div[data-testid="stChatMessage"] p { font-size: 15.5px !important; line-height: 1.6 !important; color: #E2E8F0 !important; }
        [data-testid="stChatInput"] { border-radius: 28px !important; background-color: #111827 !important; border: 1px solid #1F2937 !important; }
        #MainMenu, footer, header {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">AtlasTG AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Ultra-Fast Engine • High-Speed Production Grid</div>', unsafe_allow_html=True)

# 3. Secure Production Key Verification
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are AtlasTG, a high-speed assistant. Always give short, direct summaries. Keep answers to 1 or 2 punchy sentences max. Do not ramble."}
    ]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

if user_input := st.chat_input("Message AtlasTG..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner(""):
            # FIXED: Swapped to an active, universally supported free Groq model ID
            completion = client.chat.completions.create(
                model="gemma2-9b-it",
                messages=st.session_state.messages,
                max_tokens=100,
                temperature=0.3
            )
            bot_answer = completion.choices[0].message.content.strip()
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})



