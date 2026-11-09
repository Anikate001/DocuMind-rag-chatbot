import io

import PyPDF2

from config import CHUNK_OVERLAP, CHUNK_SIZE
from database import supabase
from embeddings import get_embedder
from text_utils import chunk_text, extract_text_from_pdf, scoped_name

BATCH_SIZE = 50  # Supabase insert batch size


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Convert text chunks to embedding vectors (all-MiniLM-L6-v2, 384 dims)."""
    embeddings = get_embedder().encode(chunks, show_progress_bar=False)
    return embeddings.tolist()


def ingest_pdf(file_bytes: bytes, filename: str, progress_callback=None,
               session_id: str | None = None) -> dict:
    """
    Full pipeline:
    1. Read the PDF
    2. Register the document (replacing an earlier upload of the same file)
    3. Extract text and chunk it
    4. Embed each chunk
    5. Store chunks + embeddings in pgvector

    The raw PDF is not stored anywhere: only its text chunks are needed for
    retrieval. With a session_id, the document is visible to that session only.

    progress_callback(step: int, message: str) is called at each stage so the
    UI can update a live progress card.
    """
    def _progress(step, msg):
        if progress_callback:
            progress_callback(step, msg)
        print(f"  [{step}/5] {msg}")

    stored_name = scoped_name(session_id, filename) if session_id else filename

    _progress(1, "Reading PDF")
    num_pages = len(PyPDF2.PdfReader(io.BytesIO(file_bytes)).pages)

    _progress(2, "Extracting text")
    text = extract_text_from_pdf(file_bytes)
    chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    if not chunks:
        raise ValueError("No text found in this PDF. Scanned (image-only) PDFs are not supported yet.")

    # Re-uploading the same file replaces it instead of duplicating its chunks
    # (its chunks are removed by the ON DELETE CASCADE foreign key).
    supabase.table("documents").delete().eq("filename", stored_name).execute()
    doc_response = supabase.table("documents").insert({"filename": stored_name}).execute()
    document_id = doc_response.data[0]["id"]

    _progress(3, f"Creating chunks ({len(chunks)} chunks from {num_pages} pages)")

    _progress(4, "Generating embeddings")
    embeddings = embed_chunks(chunks)

    _progress(5, "Storing in pgvector")
    rows = [
        {
            "document_id": document_id,
            "filename": stored_name,
            "content": chunk,
            "chunk_index": i,
            "embedding": embedding,
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    for i in range(0, len(rows), BATCH_SIZE):
        supabase.table("chunks").insert(rows[i:i + BATCH_SIZE]).execute()

    print(f"  Stored {len(rows)} chunks in pgvector")
    return {
        "filename": filename,
        "chunks": len(chunks),
        "pages": num_pages,
        "document_id": document_id,
    }
