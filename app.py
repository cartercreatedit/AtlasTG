import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="FlintLynx AI", page_icon="🐆", layout="centered")

# 2. Premium Custom CSS Injector (Changes layout to look like a modern pro app)
st.markdown("""
    <style>
        /* Force dark premium background */
        .stApp {
            background-color: #0B0F19 !important;
            color: #E2E8F0 !important;
        }
        /* Custom Header styling */
        h1 {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 5px !important;
        }
        /* Style user messages */
        [data-testid="stChatMessage"]:nth-child(even) {
            background-color: #1E293B !important;
            border-radius: 16px 16px 4px 16px !important;
            border: 1px solid #334155;
            padding: 15px !important;
            margin-bottom: 10px !important;
        }
        /* Style assistant messages */
        [data-testid="stChatMessage"]:nth-child(odd) {
            background-color: #0F172A !important;
            border-radius: 16px 16px 16px 4px !important;
            border: 1px solid #1E293B;
            padding: 15px !important;
            margin-bottom: 10px !important;
        }
        /* Style the chat input bar at the bottom */
        [data-testid="stChatInput"] {
            border-radius: 24px !important;
            background-color: #1E293B !important;
            border: 1px solid #475569 !important;
        }
        div[data-testid="stChatInput"] textarea {
            color: #FFFFFF !important;
        }
        /* Hide default Streamlit clutter */
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Clean Header UI
st.markdown("<h1 style='text-align: center;'>🐆 FlintLynx AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 15px;'>High-Speed Summary Assistant • Active Memory v1.0</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #1E293B; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

API_URL = "https://huggingface.co"

if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display Messages in Custom Containers
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 5. Live Interactive Text Input
if user_input := st.chat_input("Message FlintLynx..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    formatted_prompt = f"<|user|>\n{user_input}\nContext: Keep answers to 1 or 2 summary sentences max.<|assistant|>\n"
    
    with st.chat_message("assistant"):
        with st.spinner("FlintLynx is processing..."):
            response = requests.post(API_URL, json={"inputs": formatted_prompt})
            
            try:
                raw_text = response.json()[0]['generated_text']
                bot_answer = raw_text.split("<|assistant|>\n")[-1].strip()
            except Exception:
                bot_answer = "FlintLynx is warming up its cloud connection. Please try sending your message one more time!"
                
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})

