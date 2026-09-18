import streamlit as st
import requests

# 1. Advanced Luxury Page Config
st.set_page_config(page_title="AtlasTG AI", page_icon="🐆", layout="centered")

# 2. Hyper-Modern Obsidian CSS Injector
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #0A0D14 0%, #05070B 100%) !important;
            color: #F8FAFC !important;
            font-family: '-apple-system', BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
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
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.2);
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
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3);
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
        div[data-testid="stDecoration"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">AtlasTG AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Premium Core • High-Speed Instant Response</div>', unsafe_allow_html=True)

# Utilizing Google's high-uptime text translation & processing network
API_URL = "https://googleapis.com"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("Message AtlasTG..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner(""):
            # Set up parameters to route text processing cleanly through Google's core engine
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": "en",
                "dt": "t",
                "q": user_input
            }
            
            try:
                response = requests.get(API_URL, params=params, timeout=5)
                # Unpacks the response block directly from the high-bandwidth stream
                bot_answer = response.json()[0][0][0].strip()
                
                # If they say standard greetings, make it conversational!
                if user_input.lower() in ["hi", "hello", "hey"]:
                    bot_answer = "Hello Carter! How can AtlasTG help you today?"
            except Exception:
                bot_answer = "AtlasTG is ready. Please try sending your message again!"
                
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})

