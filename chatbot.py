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

from rag import NotesIndex, build_system_prompt, read_file, split_into_chunks

NOTES_FILE = os.getenv("NOTES_FILE", "MAI600_Course_Notes.txt")  # .txt, .md, .docx or .pdf
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def main():
    if not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY is not set. See README.md, step 1 and step 3.")
    if not os.path.exists(NOTES_FILE):
        sys.exit(f"Could not find the notes file: {NOTES_FILE}")

    with open(NOTES_FILE, "rb") as f:
        text = read_file(NOTES_FILE, f.read())
    index = NotesIndex(split_into_chunks(text, NOTES_FILE))
    client = Groq()
    history = []

    print(f"MAI600 Notes Chatbot ({MODEL}, search: {index.mode}). Type 'exit' to quit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        sources = index.search(question)
        messages = [{"role": "system", "content": build_system_prompt(sources)}]
        messages += history + [{"role": "user", "content": question}]

        print("Bot: ", end="", flush=True)
        answer = ""
        for chunk in client.chat.completions.create(model=MODEL, messages=messages, temperature=0, stream=True):
            piece = chunk.choices[0].delta.content or ""
            answer += piece
            print(piece, end="", flush=True)
        print("\n")

        history = (history + [{"role": "user", "content": question},
                              {"role": "assistant", "content": answer}])[-6:]


if __name__ == "__main__":
    main()
