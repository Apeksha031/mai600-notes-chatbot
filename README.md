# MAI600 Notes Chatbot (Groq)

A small chatbot that answers questions **only** from `MAI600_Course_Notes.txt`.
If the notes don't cover something, it says it doesn't know instead of making something up.

## Features
- **Smart search (RAG):** the notes are split into small sections. For each question the bot finds the best sections
  by keyword (BM25) *and* by meaning (embeddings, `BAAI/bge-small-en-v1.5`), then sends only those to the model.
- **Cited answers:** answers cite their sources like [1], and a "Sources" box shows the exact text used.
- **Streaming:** answers appear word by word.
- **Honest:** if the notes don't cover it, the bot says "I don't know" instead of making something up.
- **Extras:** starter questions, clear chat, upload extra notes (.txt, .md, .docx, .pdf), and a limit of
  8 questions per minute per visitor to protect your free Groq quota.

## Files
- `app.py`: the web chat page (Streamlit)
- `rag.py`: reading files, splitting notes into sections, and searching them
- `chatbot.py`: terminal version
- `MAI600_Course_Notes.txt`: the notes the bot answers from
- `requirements.txt`: Python packages needed

## Step 1: Get a Groq API key
1. Go to https://console.groq.com and sign in.
2. Click **API Keys** in the left menu, then **Create API Key**.
3. Give it a name (e.g. `mai600`), then copy the key (it starts with `gsk_`).
   You only see it once, so paste it somewhere safe. Don't share it or put it in your code.

## Step 2: Install
You need Python 3.9 or newer. In a terminal, inside this folder:
```
pip install -r requirements.txt
```

## Step 3: Set your API key
macOS / Linux:
```
export GROQ_API_KEY="gsk_your_key_here"
```
Windows (PowerShell):
```
$env:GROQ_API_KEY="gsk_your_key_here"
```
(This lasts until you close the terminal. With the web version you can paste the key in the sidebar instead.)

## Step 4: Add your notes
Download `MAI600_Course_Notes.txt` from Canvas and put it in this folder.

## Step 5: Run
Terminal version:
```
python chatbot.py
```
Web version:
```
streamlit run app.py
```
A browser tab opens at http://localhost:8501.

## Step 6: Test it (the class exercise)
| Question | What should happen |
|---|---|
| What is supervised learning? | An answer based on the notes |
| What is the campus parking fee? | "I don't know. That isn't covered in the MAI600 course notes." |

## Troubleshooting
- **"model ... has been decommissioned" or "model not found"**: Groq retires models now and then. Pick a current one from
  https://console.groq.com/docs/models and set it, e.g. `export GROQ_MODEL="openai/gpt-oss-20b"`.
- **"rate limit" / "request too large"**: the free tier limits tokens per minute. The bot only sends the 5 most relevant sections; lower `TOP_K` in `app.py` if you still hit it.
- **"Could not find the notes file"**: check the file name and that it's in the same folder, or set `NOTES_FILE` to its full path.

## Put it online (Streamlit Community Cloud, free)
1. Put these files in a GitHub repository (include `MAI600_Course_Notes.txt` if you want visitors to skip uploading it).
2. Go to https://share.streamlit.io, sign in with GitHub, and click **Create app** → **Deploy a public app from GitHub**.
3. Pick the repository, branch `main`, and main file `app.py`.
4. Click **Advanced settings**, and in **Secrets** paste:
   ```
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy**. After a minute or two you get a link like `https://your-app-name.streamlit.app`.

The key stays private in Streamlit's settings and is never in your code. To change it later: your app → **Settings** → **Secrets**.
