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
    page_title="AtlasTG AI",
    page_icon="🐆",
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
st.title("🐆 AtlasTG AI")
st.caption("Commercial Engine · High-Speed Summary Engine")

# ────────────────────────────────────────────────
# Session state for chat history
# ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am AtlasTG, your premium high-speed summary intelligence system. What can I analyze for you today?"}
    ]

# Display previous messages with custom avatars
for msg in st.session_state.messages:
    avatar_icon = "🐆" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# ────────────────────────────────────────────────
# Chat input + Groq call
# ────────────────────────────────────────────────
user_input = st.chat_input("Message AtlasTG…")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Call Groq with the official client
    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Injecting system context to keep responses to a 1-2 sentence maximum summary
        system_instruction = {"role": "system", "content": "You are AtlasTG, a helpful commercial AI assistant. Always keep answers very short, concise, and summary-focused. Limit responses strictly to 1 or 2 sentences max. Do not ramble."}
        
        full_messages = [system_instruction] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=full_messages,
            temperature=0.3,
            max_tokens=150,
        )

        # Extract text the official way (no .json(), no dict indexing)
        reply = completion.choices[0].message.content

    except Exception as e:
        reply = f"⚠️ Error talking to Groq: {e}"

    # Show and store assistant reply with custom leopard avatar
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant", avatar="🐆"):
        st.markdown(reply)
