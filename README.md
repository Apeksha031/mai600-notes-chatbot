# MAI600 Notes Chatbot (Groq)

A small chatbot that answers questions **only** from `MAI600_Course_Notes.txt`.
If the notes don't cover something, it says it doesn't know instead of making something up.

It works by pasting the whole notes file into the model's instructions, then sending your question
to a fast open model hosted on Groq.

## Files
- `chatbot.py`: terminal version (simplest)
- `app.py`: web chat page (Streamlit), lets you upload the notes in the browser
- `requirements.txt`: the two Python packages needed

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
  https://console.groq.com/docs/models and set it, e.g. `export GROQ_MODEL="llama-3.1-8b-instant"`.
- **"rate limit" / "request too large"**: the free tier limits tokens per minute. If your notes are very long, wait a minute
  and retry, or try a different model.
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
