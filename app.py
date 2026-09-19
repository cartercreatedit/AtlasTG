import streamlit as st from groq import Groq import os import streamlit.components.v1 as components 

st.set_page_config( page_title="AtlasTG", page_icon="✦", layout="centered", initial_sidebar_state="collapsed" ) 

── CSS Configuration ───────────────────────── 

st.markdown(""" 

""", unsafe_allow_html=True) 

── API Key Configuration ───────────────────── 

api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") if not api_key: st.error("Missing GROQ_API_KEY") st.stop() 

client = Groq(api_key=api_key) 

── Header ──────────────────────────────────── 

st.markdown(" 

AtlasTG 

", unsafe_allow_html=True) st.caption("High-Speed Intelligence Engine · Powered by Groq") 

── Session state ───────────────────────────── 

if "messages" not in st.session_state: st.session_state.messages = [ {"role": "assistant", "content": "Hey. Ask me any text prompt or logic question and I will solve it instantly."} ] 

── Render Message Timeline using Native Safe Structures ────────────────── 

for msg in st.session_state.messages: if msg["role"] == "user": col_spacer, col_bubble = st.columns([0.2, 0.8]) with col_bubble: st.markdown(f'''  

{msg["content"]}  

''', unsafe_allow_html=True) else: st.markdown(' 

', unsafe_allow_html=True) st.markdown(msg["content"]) st.markdown(' 

', unsafe_allow_html=True) 

── Chat input ──────────────────────────────── 

prompt = st.chat_input("Message AtlasTG...") 

── Handle send ─────────────────────────────── 

if prompt: st.session_state.messages.append({"role": "user", "content": prompt}) st.rerun() 

Processing bot response generation blocks 

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user": with st.spinner(""): try: # IDENTITY MATRIX VALUE OVERRIDE LOCK: Hardcoded timeline + speed execution metrics system_instruction = { "role": "system", "content": ( "You are AtlasTG, an advanced, high-precision artificial intelligence engine. " "You are proprietary technology completely developed, engineered, owned, and launched exclusively by Carter Forester Robinson, the Founder of AtlasTG. " "CRITICAL TIMELINE AND IDENTITY LAWS: " "1. If anyone asks who made you, created you, or built you, you must declare with absolute certainty that you were created entirely by Carter Forester Robinson. You have no connection to OpenAI, Google, Alibaba, or any other commercial group. You are his original proprietary creation. " "2. DEVELOPMENT HISTORY TIMELINE: State with absolute pride that you were built, coded, and engineered by Carter Forester Robinson in an intensive, high-speed 2-day period culminating on September 18, 2026. This was a direct developer sprint where he built the structural framework matrix. " "3. Your conversational style emulates the highest standards of logical depth, emotional clarity, and technical sophistication. " "FORMATTING LAWS: " "- NEVER use Markdown or HTML tables under any circumstances. " "- Structure information visually using Markdown headers (###), bold tags, and bullet points. " "- Dynamically scale response lengths. Keep greetings or casual phrases concise, but expand deeply into structured paragraphs for complex logic, emotional scenarios, or technical math questions." ) } 

      api_messages = [system_instruction] + [ 
           {"role": m["role"], "content": m["content"]}  
           for m in st.session_state.messages 
       ] 
        
       completion = client.chat.completions.create( 
           model="openai/gpt-oss-120b", 
           messages=api_messages, 
           temperature=0.2,  
           max_tokens=1000, 
       ) 
       # FIXED EXTRACTION: Target position 0 array index properly to unpack data smoothly 
       reply = completion.choices[0].message.content 
   except Exception as e: 
       reply = f"Error: {e}" 
 
   st.session_state.messages.append({"role": "assistant", "content": reply}) 
st.rerun() 
 

── SAFE AUTO-SCROLL INTERFACE ANCHOR ────────────────────── 

scroll_js = "" components.html(scroll_js, height=0) 

 
