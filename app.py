import streamlit as st
import requests

# 1. Set up the sleek browser tab layout
st.set_page_config(page_title="FlintLynx AI", page_icon="🐆")
st.title("🐆 FlintLynx AI Chat")
st.write("A permanent, high-speed AI assistant.")

# 2. This connects your site to the free Hugging Face API brain
API_URL = "https://huggingface.co"

# 3. Create the chat memory storage
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display past chat history bubbles on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 5. Handle the live user text box at the bottom
if user_input := st.chat_input("Ask FlintLynx a question..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Format prompt for the model
    formatted_prompt = f"<|user|>\n{user_input}\nContext: Keep answers to 1 or 2 summary sentences max.<|assistant|>\n"
    
    with st.chat_message("assistant"):
        with st.spinner("FlintLynx is thinking..."):
            # Securely send the prompt over the web
            response = requests.post(API_URL, json={"inputs": formatted_prompt})
            
            try:
                raw_text = response.json()[0]['generated_text']
                bot_answer = raw_text.split("<|assistant|>\n")[-1].strip()
            except Exception:
                bot_answer = "FlintLynx is waking up its cloud connection. Please try typing your message one more time!"
                
            st.write(bot_answer)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_answer})
