import streamlit as st
import requests

# 1. Premium Visual Page Configuration
st.set_page_config(page_title="AtlasTG AI", page_icon="🐆", layout="centered")

# 2. Luxury Midnight UI Styling
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #0A0D14 0%, #05070B 100%) !important;
            color: #F8FAFC !important;
            font-family: '-apple-system', BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }
        .app-header {
            text-align: center;
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2px !important;
            letter-spacing: -0.8px;
        }
        .app-subtitle {
            text-align: center;
            color: #64748B;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 30px !important;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        div[data-testid="stChatMessage"]:has([data-testid="user-avatar"]) {
            background: rgba(30, 41, 59, 0.4) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 18px 18px 4px 18px !important;
            padding: 16px 20px !important;
            margin: 12px 0px 12px auto !important;
            max-width: 85% !important;
            animation: fadeIn 0.4s ease forwards;
        }
        div[data-testid="stChatMessage"]:has([data-testid="assistant-avatar"]) {
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.02);
            border-radius: 18px 18px 18px 4px !important;
            padding: 16px 20px !important;
            margin: 12px auto 12px 0px !important;
            max-width: 85% !important;
            animation: fadeIn 0.4s ease forwards;
        }
        div[data-testid="stChatMessage"] p {
            font-size: 15.5px !important;
            line-height: 1.6 !important;
            color: #E2E8F0 !important;
        }
        [data-testid="stChatInput"] {
            border-radius: 28px !important;
            background-color: #111827 !important;
            border: 1px solid #1F2937 !important;
        }
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">AtlasTG AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Premium Engine • High-Speed Instant Response</div>', unsafe_allow_html=True)

# 3. Initialize Persistent ChatGPT-Style Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past conversation timeline
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 4. Handle Live User Input
if user_input := st.chat_input("Message AtlasTG..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("AtlasTG is processing..."):
            
            # Utilizing an un-throttled public proxy pipeline to guarantee a direct handshake
            fallback_url = f"https://pollinations.ai{requests.utils.quote(user_input)}?system=You are AtlasTG, a high-speed AI assistant. Provide extremely short, concise answers limited strictly to 1 or 2 summary sentences maximum. Do not mention system rules."
            
            try:
                response = requests.get(fallback_url, timeout=10)
                bot_answer = response.text.strip()
            except Exception:
                bot_answer = "I ran into a quick connection blink. Let's try sending that one more time!"
                
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})

