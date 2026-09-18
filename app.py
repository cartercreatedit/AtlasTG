import streamlit as st
import requests

# 1. Advanced Page Config
st.set_page_config(page_title="FlintLynx AI", page_icon="🐆", layout="centered")

# 2. Hyper-Modern Luxury CSS Injector
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
            -webkit-backdrop-filter: blur(12px);
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
            -webkit-backdrop-filter: blur(12px);
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
            font-weight: 400 !important;
        }
        [data-testid="stChatInput"] {
            border-radius: 28px !important;
            background-color: #111827 !important;
            border: 1px solid #1F2937 !important;
            padding: 4px 8px !important;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.7) !important;
            transition: border-color 0.3s ease;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #4B5563 !important;
        }
        #MainMenu, footer, header {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">FlintLynx AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Optimized Core Model • High-Speed Summary Engine</div>', unsafe_allow_html=True)

API_URL = "https://huggingface.co"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("Message FlintLynx..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    formatted_prompt = f"<|user|>\n{user_input}\nContext: Keep answers to 1 or 2 summary sentences max.<|assistant|>\n"
    
    with st.chat_message("assistant"):
        with st.spinner("FlintLynx is processing..."):
            payload = {
                "inputs": formatted_prompt,
                "options": {"wait_for_model": True}
            }
            
            # PROTECTED NETWORKING BLOCK: Catches connection loss without crashing
            try:
                response = requests.post(API_URL, json=payload, timeout=10)
                raw_data = response.json()
                
                if isinstance(raw_data, list):
                    text_block = raw_data['generated_text']
                else:
                    text_block = raw_data['generated_text']
                
                bot_answer = text_block.split("<|assistant|>\n")[-1].strip()
            except requests.exceptions.RequestException:
                bot_answer = "⚠️ FlintLynx is experiencing heavy network traffic or lost connection to its server brain. Please try sending your message again in a few seconds!"
            except Exception:
                bot_answer = "⚠️ Having trouble parsing the cloud data stream. Let's try sending that one more time."
                
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})

