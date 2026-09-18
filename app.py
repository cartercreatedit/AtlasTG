import streamlit as st
from groq import Groq

# ────────────────────────────────────────────────
# PASTE YOUR GROQ API KEY HERE (starts with gsk_)
# ────────────────────────────────────────────────
GROQ_API_KEY = "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"


# ────────────────────────────────────────────────
# Page + Dark Theme
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Groq Chat",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Force dark premium theme */
    .stApp {
        background: linear-gradient(180deg, #0b0f19 0%, #111827 100%);
        color: #e5e7eb;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 900px;
    }
    h1, h2, h3, h4 {
        color: #f9fafb !important;
        font-weight: 600;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1f2937 !important;
        color: #f3f4f6 !important;
        border: 1px solid #374151 !important;
        border-radius: 10px !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
    }
    .stChatMessage {
        background-color: #1f2937 !important;
        border-radius: 12px !important;
        border: 1px solid #374151 !important;
    }
    div[data-testid="stMarkdownContainer"] p {
        color: #e5e7eb;
    }
    /* Hide Streamlit branding for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────
st.title("⚡ Groq Chat")
st.caption("Powered by llama-3.1-8b-instant · Official Groq SDK")

# ────────────────────────────────────────────────
# Session state for chat history
# ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ────────────────────────────────────────────────
# Chat input + Groq call
# ────────────────────────────────────────────────
user_input = st.chat_input("Type your message…")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call Groq with the official client
    try:
        client = Groq(api_key=GROQ_API_KEY)

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        # Extract text the official way (no .json(), no dict indexing)
        reply = completion.choices[0].message.content

    except Exception as e:
        reply = f"⚠️ Error talking to Groq: {e}"

    # Show and store assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

