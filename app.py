import streamlit as st
import torch
from transformers import pipeline

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
st.markdown('<div class="app-subtitle">Self-Contained Local Core Engine • 100% Uptime Guaranteed</div>', unsafe_allow_html=True)

# 3. Load Your Verified Model Pipeline directly inside the server memory
@st.cache_resource
def load_local_ai():
    return pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device="cpu", # Swapped to CPU since Streamlit free servers run on high-performance cloud CPUs
        torch_dtype=torch.float32
    )

ai_pipeline = load_local_ai()

# 4. Initialize History Matrix exactly like your Colab script
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are AtlasTG, a high-speed assistant. Always give short, direct summaries. Keep answers to 1 or 2 punchy sentences max. Do not ramble."
        }
    ]

# Render chat timeline tracking history rows
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# 5. Process User Input exactly like your old While Loop
if user_input := st.chat_input("Message AtlasTG..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Format the prompt structure identically to your running script
    formatted_prompt = ai_pipeline.tokenizer.apply_chat_template(st.session_state.messages, tokenize=False, add_generation_prompt=True)
    
    with st.chat_message("assistant"):
        with st.spinner(""):
            response = ai_pipeline(
                formatted_prompt,
                max_new_tokens=40,
                do_sample=False
            )
            
            # YOUR PERMANENT CONTAINER FIX: Grabs the text data from the list stream cleanly
            if isinstance(response, list) and len(response) > 0:
                raw_text = response[0]['generated_text']
            elif isinstance(response, dict):
                raw_text = response['generated_text']
            else:
                raw_text = response

            bot_answer = raw_text.split("<|assistant|>\n")[-1].strip()

            # Clean copy leak strings exactly like your notebook code
            if "\nYou:" in bot_answer:
                bot_answer = bot_answer.split("\nYou:")[0].strip()
            if "\nCarter:" in bot_answer:
                bot_answer = bot_answer.split("\nCarter:")[0].strip()
                
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})



