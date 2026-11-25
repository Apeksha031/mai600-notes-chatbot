"""
rag.py: finds the parts of the notes that answer a question.

This is "retrieval-augmented generation" (RAG):
  1. Split the notes into small overlapping chunks.
  2. For each question, find the most relevant chunks two ways:
       - Keyword search (BM25): good at exact terms like "A3" or "Turnitin".
       - Meaning search (embeddings): finds chunks with the same meaning even
         when the words differ ("group project deadline" -> "A3 ... due").
  3. Combine both rankings (reciprocal rank fusion) and send the best chunks
     to the language model along with the question.
"""

import io
import re

import numpy as np
from rank_bm25 import BM25Okapi

EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # small, free, runs on CPU

STOPWORDS = set("""a an and are as at be by can do does for from how i in is it
of on or that the this to was what when where which who why will with you your""".split())


def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


# ---- Reading files --------------------------------------------------------

def read_file(name, data):
    """Turn an uploaded .txt, .md, .docx or .pdf file (bytes) into plain text."""
    name = name.lower()
    if name.endswith(".docx"):
        import docx
        doc = docx.Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        return "\n\n".join(p for p in parts if p.strip())
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


# ---- Chunking -------------------------------------------------------------

def split_into_chunks(text, source, size=900, overlap=150):
    """Split text into ~size-character chunks that overlap a little,
    so a sentence cut at a boundary still appears whole in one chunk."""
    paras = [re.sub(r"[ \t]+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paras = [p for p in paras if p]
    chunks, current = [], ""
    for para in paras:
        # Very long paragraphs (e.g. big tables) are cut into pieces
        while len(para) > size:
            cut = para.rfind(" ", 0, size)
            cut = cut if cut > size // 2 else size
            pieces = para[:cut]
            para = para[cut - overlap:] if cut > overlap else para[cut:]
            if current:
                chunks.append(current)
                current = ""
            chunks.append(pieces)
        if current and len(current) + len(para) > size:
            chunks.append(current)
            current = current[-overlap:] + " "  # carry a little context over
        current += para + "\n"
    if current.strip():
        chunks.append(current)
    return [{"text": c.strip(), "source": source} for c in chunks if c.strip()]


# ---- The search index -----------------------------------------------------

class NotesIndex:
    def __init__(self, chunks):
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
        self.embedder = None
        self.vectors = None
        try:
            from fastembed import TextEmbedding
            self.embedder = TextEmbedding(EMBED_MODEL)
            self.vectors = self._embed([c["text"] for c in chunks])
        except Exception as e:  # no internet / model download failed
            print(f"Meaning search unavailable, using keyword search only: {e}")
            self.embedder = None

    @property
    def mode(self):
        return "meaning + keyword" if self.embedder else "keyword only"

    def _embed(self, texts):
        vecs = np.array(list(self.embedder.embed(texts)))
        return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

    def search(self, query, k=5):
        """Return the k best chunks for the query, best first."""
        rankings = [np.argsort(-self.bm25.get_scores(tokenize(query)))]
        if self.embedder is not None:
            q = self._embed([query])[0]
            rankings.append(np.argsort(-(self.vectors @ q)))
        # Reciprocal rank fusion: a chunk ranked high by either method wins
        fused = {}
        for ranking in rankings:
            for rank, idx in enumerate(ranking):
                fused[idx] = fused.get(idx, 0) + 1 / (60 + rank)
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return [self.chunks[i] for i in best]


# ---- The prompt -----------------------------------------------------------

NOT_FOUND = "I don't know. That isn't covered in the MAI600 course notes."


def build_system_prompt(chunks):
    sources = "\n\n".join(
        f"[{i}] (from {c['source']})\n{c['text']}" for i, c in enumerate(chunks, 1)
    )
    return f"""You are a friendly, precise study assistant for the MAI600 course.

Answer the student's question using ONLY the numbered excerpts from the course notes below.

Rules:
- If the excerpts answer the question, give a clear, well-organised answer. Use short paragraphs or bullet points when helpful.
- After each fact, cite the excerpt it came from in square brackets, like [1] or [2][3].
- If the excerpts do not contain the answer, reply exactly: "{NOT_FOUND}" and nothing else.
- Never use outside knowledge, and never guess or invent facts, dates, numbers or policies.
- Do not mention "excerpts" to the student; just answer and cite.

Course note excerpts:
{sources}"""
