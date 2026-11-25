"""
MAI600 Notes Chatbot (terminal version)
---------------------------------------
Answers questions ONLY from your course notes file, using a Groq-hosted model.

Run:   python chatbot.py
Quit:  type  exit  (or press Ctrl+C)
"""

import os
import sys

from groq import Groq

# ---- Settings you can change -------------------------------------------
NOTES_FILE = os.getenv("NOTES_FILE", "MAI600_Course_Notes.txt")  # path to your notes
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")       # any chat model listed at console.groq.com/docs/models
# -------------------------------------------------------------------------

NOT_FOUND = "I don't know. That isn't covered in the MAI600 course notes."


def load_notes(path):
    """Read the notes file, or stop with a friendly message if it's missing."""
    if not os.path.exists(path):
        sys.exit(f"Could not find the notes file: {path}\n"
                 "Put MAI600_Course_Notes.txt in this folder (or set NOTES_FILE).")
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def build_system_prompt(notes):
    """The rules the model must follow, with the notes pasted in as context."""
    return f"""You are a helpful study assistant for the MAI600 course.

Answer the student's question using ONLY the course notes between the <notes> tags.
Rules:
- If the answer is in the notes, answer clearly and concisely in your own words.
- If the notes do not contain the answer, reply exactly: "{NOT_FOUND}"
- Never use outside knowledge, and never guess or make up facts, numbers, or policies.

<notes>
{notes}
</notes>"""


def ask(client, system_prompt, history, question):
    """Send the question (plus earlier conversation) to Groq and return the answer."""
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
    system_prompt = build_system_prompt(notes)
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

        answer = ask(client, system_prompt, history, question)
        print(f"Bot: {answer}\n")

        # Remember the last few turns so follow-up questions make sense
        history += [{"role": "user", "content": question},
                    {"role": "assistant", "content": answer}]
        history = history[-6:]


if __name__ == "__main__":
    main()
