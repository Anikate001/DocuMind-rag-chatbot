"""Pure text helpers shared by the app and the evaluation harness.

Kept free of Supabase / Streamlit imports so they can be used and tested
without any credentials.
"""
import io

import PyPDF2


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap  # overlap so context isn't lost at boundaries
    return chunks


def format_context(chunks: list[dict]) -> tuple[str, list[str]]:
    """
    Format retrieved chunks into a context string for the LLM
    and return citation references.
    """
    context_parts = []
    citations = []

    for i, chunk in enumerate(chunks):
        source = f"[{i+1}] {chunk['filename']} (chunk {chunk['chunk_index']+1})"
        citations.append(source)
        context_parts.append(f"Source {i+1} ({chunk['filename']}):\n{chunk['content']}")

    context = "\n\n---\n\n".join(context_parts)
    return context, citations
