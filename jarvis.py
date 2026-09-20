import streamlit as st
from groq import Groq
import datetime

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="✦",
    layout="centered"
)

# =========================
# STYLE
# =========================

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0a0a0a !important;
}

.stApp {
    background-color: #0a0a0a;
    color: white;
}

.block-container {
    max-width: 760px;
    padding-top: 45px;
}

.title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    letter-spacing: 8px;
}

.subtitle {
    text-align: center;
    color: #777;
    letter-spacing: 3px;
    margin-bottom: 35px;
}

.core {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 2px solid #00f2fe;
    margin: 20px auto 40px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
        0 0 15px #00f2fe,
        0 0 40px rgba(0,242,254,.25),
        inset 0 0 25px rgba(0,242,254,.15);
}

.inner {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    border: 2px solid #00f2fe;
    box-shadow:
        0 0 15px #00f2fe,
        inset 0 0 20px rgba(0,242,254,.25);
}

.chat {
    background: #111;
    border: 1px solid #222;
    border-radius: 14px;
    padding: 16px;
    margin: 10px 0;
}

.user {
    color: #00f2fe;
}

.jarvis {
    color: white;
}

.small {
    text-align: center;
    color: #555;
    font-size: 12px;
    margin-top: 25px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# GROQ
# =========================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = ""

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

# =========================
# MEMORY
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# TIME
# =========================

now = datetime.datetime.now()

current_time = now.strftime("%I:%M %p")
current_date = now.strftime("%A, %B %d, %Y")

# =========================
# HEADER
# =========================

st.markdown(
    '<div class="title">J.A.R.V.I.S.</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">PERSONAL AI SYSTEM</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="core">
    <div class="inner"></div>
</div>
""", unsafe_allow_html=True)

# =========================
# QUICK BUTTONS
# =========================

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("TIME", use_container_width=True):
        st.session_state.messages.append(
            {"role": "user", "content": "What time is it?"}
        )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"The current time is {current_time}."
            }
        )
        st.rerun()

with c2:
    if st.button("DATE", use_container_width=True):
        st.session_state.messages.append(
            {"role": "user", "content": "What is today's date?"}
        )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Today is {current_date}."
            }
        )
        st.rerun()

with c3:
    if st.button("CLEAR", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =========================
# CHAT HISTORY
# =========================

for message in st.session_state.messages:

    if message["role"] == "user":
        st.markdown(
            f"""
            <div class="chat user">
            <b>You:</b> {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f"""
            <div class="chat jarvis">
            <b>J.A.R.V.I.S.:</b> {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# USER INPUT
# =========================

prompt = st.chat_input("Speak to J.A.R.V.I.S...")

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    if not client:

        answer = (
            "My Groq API key hasn't been connected yet. "
            "Add GROQ_API_KEY in Streamlit Secrets."
        )

    else:

        try:

            messages = [
                {
                    "role": "system",
                    "content": f"""
You are J.A.R.V.I.S., a highly capable personal AI assistant.

Current date:
{current_date}

Current time:
{current_time}

You can communicate in many languages.
Always respond in the language the user uses unless they request another language.

Be natural, concise and helpful.

You have access to Groq's built-in tools when available, so use
them when the user needs current information.

Never claim that you performed an action unless it actually happened.

The user may ask you to control their computer. Explain what can
and cannot actually be done by the current application.
"""
                }
            ]

            messages.extend(
                st.session_state.messages[-12:]
            )

            response = client.chat.completions.create(
                model="groq/compound",
                messages=messages,
                temperature=0.7
            )

            answer = response.choices[0].message.content

        except Exception as e:

            answer = f"Groq error: {str(e)}"

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    st.rerun()

st.markdown(
    '<div class="small">GROQ • MULTILINGUAL • WEB SEARCH • J.A.R.V.I.S.</div>',
    unsafe_allow_html=True
)
