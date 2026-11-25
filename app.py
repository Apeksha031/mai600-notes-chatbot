"""
MAI600 Notes Chatbot (web version, built with Streamlit)
Run:  streamlit run app.py
"""

import hashlib
import os
import time

import streamlit as st
from groq import Groq

from rag import NOT_FOUND, NotesIndex, build_system_prompt, read_file, split_into_chunks

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")  # see console.groq.com/docs/models
NOTES_FILES = ["MAI600_Course_Notes.txt"]  # notes bundled with the app
TOP_K = 5             # how many note chunks to send with each question
MAX_PER_MINUTE = 8    # questions per visitor per minute (protects your free Groq quota)
STARTERS = [
    "What topics does this unit cover?",
    "When is assessment A3 due?",
    "What is the late submission penalty?",
    "What is the campus parking fee?",
]

st.set_page_config(page_title="MAI600 Study Assistant", page_icon="🎓", layout="centered")


# ---- Setup ----------------------------------------------------------------

def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:  # no secrets file on your laptop
        key = ""
    return key or os.getenv("GROQ_API_KEY") or st.sidebar.text_input("Groq API key", type="password")


@st.cache_resource(show_spinner="Reading the notes...")
def build_index(files):
    """files: tuple of (name, text). Cached so it only runs once per set of notes."""
    chunks = []
    for name, text in files:
        chunks += split_into_chunks(text, name)
    return NotesIndex(chunks)


def load_notes():
    files = []
    for path in NOTES_FILES:
        if os.path.exists(path):
            with open(path, encoding="utf-8", errors="ignore") as f:
                files.append((path, f.read()))
    uploads = st.sidebar.file_uploader(
        "Add notes (.txt, .md, .docx, .pdf)", type=["txt", "md", "docx", "pdf"],
        accept_multiple_files=True,
    )
    for up in uploads or []:
        files.append((up.name, read_file(up.name, up.getvalue())))
    return tuple(files)


def rate_limited():
    now = time.time()
    recent = [t for t in st.session_state.get("asked_at", []) if now - t < 60]
    st.session_state.asked_at = recent
    if len(recent) >= MAX_PER_MINUTE:
        return True
    recent.append(now)
    return False


# ---- Page -----------------------------------------------------------------

st.title("🎓 MAI600 Study Assistant")
st.caption("Ask anything about the MAI600 course notes. Answers come only from the notes, with sources.")

api_key = get_api_key()
files = load_notes()

if not api_key:
    st.info("Add your Groq API key in the sidebar to start.")
    st.stop()
if not files:
    st.info("Upload your notes in the sidebar, or put MAI600_Course_Notes.txt next to app.py.")
    st.stop()

index = build_index(files)
client = Groq(api_key=api_key)

with st.sidebar:
    st.success(f"{len(files)} file(s) loaded, {len(index.chunks)} sections indexed")
    st.caption(f"Search: {index.mode} · Model: {MODEL}")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()

if "history" not in st.session_state:
    st.session_state.history = []


def show_sources(sources):
    with st.expander(f"📚 Sources ({len(sources)})"):
        for i, c in enumerate(sources, 1):
            snippet = c["text"] if len(c["text"]) < 500 else c["text"][:500] + "..."
            st.markdown(f"**[{i}]** _{c['source']}_")
            st.text(snippet)


# Show the conversation so far
for msg in st.session_state.history:
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
        st.markdown(msg["content"])
        if msg.get("sources"):
            show_sources(msg["sources"])

# Starter questions for an empty chat
question = None
if not st.session_state.history:
    st.markdown("**Try asking:**")
    cols = st.columns(2)
    for i, q in enumerate(STARTERS):
        if cols[i % 2].button(q, use_container_width=True):
            question = q

question = st.chat_input("Ask about MAI600...") or question


def stream_answer(messages):
    """Yield the answer piece by piece as Groq generates it."""
    extra = {"reasoning_effort": "low"} if "gpt-oss" in MODEL else {}
    stream = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0, stream=True, **extra
    )
    for chunk in stream:
        piece = chunk.choices[0].delta.content
        if piece:
            yield piece


if question:
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🎓"):
        if rate_limited():
            answer, sources = "You're asking very fast. Please wait a minute and try again.", []
            st.markdown(answer)
        else:
            # Include the previous question so follow-ups like "and A4?" still find the right notes
            past = [m["content"] for m in st.session_state.history if m["role"] == "user"][-1:]
            sources = index.search(" ".join(past + [question]), k=TOP_K)

            messages = [{"role": "system", "content": build_system_prompt(sources)}]
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.history[-6:]]
            messages.append({"role": "user", "content": question})
            try:
                answer = st.write_stream(stream_answer(messages))
            except Exception as e:
                answer = f"Sorry, something went wrong talking to Groq: {e}"
                st.error(answer)
                sources = []
            if NOT_FOUND.split(".")[0] in answer:
                sources = []  # nothing relevant, so don't show sources
            if sources:
                show_sources(sources)

    st.session_state.history += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer, "sources": sources},
    ]
