"""
MAI600 Notes Chatbot (terminal version)
---------------------------------------
Answers questions ONLY from your course notes file, using a Groq-hosted model.

Run:   python chatbot.py
Quit:  type  exit  (or press Ctrl+C)
"""

import os
import re
import sys
from collections import Counter

from groq import Groq

# ---- Settings you can change -------------------------------------------
NOTES_FILE = os.getenv("NOTES_FILE", "MAI600_Course_Notes.txt")  # path to your notes
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")            # any chat model listed at console.groq.com/docs/models
TOP_CHUNKS = 5  # how many pieces of the notes to send with each question
# -------------------------------------------------------------------------

NOT_FOUND = "I don't know. That isn't covered in the MAI600 course notes."


def load_notes(path):
    """Read the notes file, or stop with a friendly message if it's missing."""
    if not os.path.exists(path):
        sys.exit(f"Could not find the notes file: {path}\n"
                 "Put MAI600_Course_Notes.txt in this folder (or set NOTES_FILE).")
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---- Finding the relevant part of the notes -----------------------------
# Groq's free tier only accepts a limited number of words per minute, so long
# notes can't be sent in full. Instead we split them into pieces ("chunks")
# and send only the pieces that share the most words with the question.

STOPWORDS = set("""a an and are as at be by can do does for from how i in is it
of on or that the this to was what when where which who why will with you your""".split())


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


def split_into_chunks(notes, size=1500):
    """Group paragraphs into chunks of about `size` characters."""
    chunks, current = [], ""
    for para in notes.split("\n\n"):
        if current and len(current) + len(para) > size:
            chunks.append(current)
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(current)
    return chunks


def find_relevant(question, chunks, k=TOP_CHUNKS):
    """Return the k chunks that best match the question's words."""
    q_words = set(words(question))
    # Words that appear in few chunks count more than very common words
    doc_freq = Counter(w for c in chunks for w in set(words(c)))
    def score(chunk):
        counts = Counter(words(chunk))
        return sum(counts[w] / doc_freq[w] for w in q_words if w in counts)
    ranked = sorted(chunks, key=score, reverse=True)
    return "\n---\n".join(ranked[:k])


def build_system_prompt(notes):
    """The rules the model must follow, with the relevant notes pasted in."""
    return f"""You are a helpful study assistant for the MAI600 course.

Answer the student's question using ONLY the course notes between the <notes> tags.
Rules:
- If the answer is in the notes, answer clearly and concisely in your own words.
- If the notes do not contain the answer, reply exactly: "{NOT_FOUND}"
- Never use outside knowledge, and never guess or make up facts, numbers, or policies.

<notes>
{notes}
</notes>"""


def ask(client, chunks, history, question):
    """Send the question, the matching notes and earlier chat to Groq; return the answer."""
    system_prompt = build_system_prompt(find_relevant(question, chunks))
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,  # 0 = most factual, least creative
    )
    return response.choices[0].message.content.strip()


def main():
    if not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY is not set. See README.md, step 1 and step 3.")

    notes = load_notes(NOTES_FILE)
    chunks = split_into_chunks(notes)
    client = Groq()  # reads GROQ_API_KEY from your environment
    history = []

    print(f"MAI600 Notes Chatbot ({MODEL}). Loaded {len(notes):,} characters of notes.")
    print("Ask a question, or type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        answer = ask(client, chunks, history, question)
        print(f"Bot: {answer}\n")

        # Remember the last few turns so follow-up questions make sense
        history += [{"role": "user", "content": question},
                    {"role": "assistant", "content": answer}]
        history = history[-6:]


if __name__ == "__main__":
    main()
