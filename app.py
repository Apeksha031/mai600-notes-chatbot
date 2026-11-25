"""
MAI600 Notes Chatbot (web version, built with Streamlit)
Run:  streamlit run app.py
"""

import os

import streamlit as st
from groq import Groq

from chatbot import MODEL, NOTES_FILE, build_system_prompt

st.set_page_config(page_title="MAI600 Notes Chatbot", page_icon="📘")
st.title("📘 MAI600 Notes Chatbot")
st.caption(f"Answers only from the course notes. Model: {MODEL}")

def get_secret_key():
    """On Streamlit Cloud the key lives in the app's Secrets settings."""
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except Exception:  # no secrets file on your laptop, that's fine
        return ""


# API key: Streamlit secrets, then the environment, then typed into the sidebar
api_key = get_secret_key() or os.getenv("GROQ_API_KEY") or st.sidebar.text_input("Groq API key", type="password")

# Notes: from the file next to this script, or uploaded in the sidebar
uploaded = st.sidebar.file_uploader("Notes file (.txt)", type="txt")
if uploaded:
    notes = uploaded.read().decode("utf-8", errors="ignore")
elif os.path.exists(NOTES_FILE):
    with open(NOTES_FILE, encoding="utf-8", errors="ignore") as f:
        notes = f.read()
else:
    notes = None

if not api_key:
    st.info("Add your Groq API key in the sidebar to start.")
    st.stop()
if not notes:
    st.info(f"Upload your notes in the sidebar, or put {NOTES_FILE} next to app.py.")
    st.stop()

st.sidebar.success(f"Notes loaded ({len(notes):,} characters)")

client = Groq(api_key=api_key)
system_prompt = build_system_prompt(notes)

if "history" not in st.session_state:
    st.session_state.history = []

# Show the conversation so far
for msg in st.session_state.history:
    st.chat_message(msg["role"]).write(msg["content"])

if question := st.chat_input("Ask about the MAI600 notes..."):
    st.chat_message("user").write(question)
    messages = [{"role": "system", "content": system_prompt}]
    messages += st.session_state.history[-6:]
    messages.append({"role": "user", "content": question})

    with st.spinner("Thinking..."):
        try:
            response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            answer = f"Error from Groq: {e}"

    st.chat_message("assistant").write(answer)
    st.session_state.history += [{"role": "user", "content": question},
                                 {"role": "assistant", "content": answer}]
