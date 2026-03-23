import os
import io
import PyPDF2
import numpy as np
from sentence_transformers import SentenceTransformer
from database import supabase

# Load embedding model once (free, runs locally, 384 dims)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

BUCKET_NAME = "documents"

def _ensure_bucket_exists():
    """Create the storage bucket if it doesn't already exist (via REST API)."""
    import requests
    from config import SUPABASE_URL, SUPABASE_KEY
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        # Check existing buckets
        r = requests.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers, timeout=5)
        bucket_ids = [b["id"] for b in r.json()] if r.status_code == 200 else []
        if BUCKET_NAME not in bucket_ids:
            r2 = requests.post(
                f"{SUPABASE_URL}/storage/v1/bucket",
                json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": True},
                headers=headers, timeout=5
            )
            if r2.status_code == 200:
                print(f"  Created storage bucket '{BUCKET_NAME}'")
            else:
                print(f"  Bucket creation response: {r2.status_code} {r2.text}")
    except Exception as e:
        print(f"  Bucket check/create note: {e}")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap  # overlap so context isn't lost at boundaries
    return chunks

def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Convert text chunks to embedding vectors."""
    embeddings = embedder.encode(chunks, show_progress_bar=True)
    return embeddings.tolist()

def ingest_pdf(file_bytes: bytes, filename: str, progress_callback=None) -> dict:
    """
    Full pipeline:
    1. Upload raw PDF to Supabase Storage
    2. Extract text
    3. Chunk it
    4. Embed each chunk
    5. Store chunks + embeddings in pgvector

    progress_callback(step: int, message: str) — optional function
    called at each stage so the UI can update a live progress card.
    """
    def _progress(step, msg):
        if progress_callback:
            progress_callback(step, msg)
        print(f"  [{step}/5] {msg}")

    _progress(0, f"Starting ingestion of {filename}")

    # Step 1 — Try uploading raw PDF to Storage (optional — fails gracefully
    #          if the API key lacks Storage permissions)
    file_url = None
    _progress(1, "Uploading to storage")
    try:
        _ensure_bucket_exists()
        storage_path = f"pdfs/{filename}"
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                file_bytes,
                {"content-type": "application/pdf"}
            )
        except Exception as upload_err:
            if "Duplicate" in str(upload_err) or "already exists" in str(upload_err):
                supabase.storage.from_(BUCKET_NAME).remove([storage_path])
                supabase.storage.from_(BUCKET_NAME).upload(
                    storage_path,
                    file_bytes,
                    {"content-type": "application/pdf"}
                )
            else:
                raise
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        print(f"  PDF uploaded to Storage: {file_url}")
    except Exception as storage_err:
        # Storage is optional — the RAG pipeline works without it
        print(f"  Storage upload skipped (not critical): {storage_err}")
        file_url = None

    # Step 2 — Save document metadata
    _progress(2, "Extracting text")
    insert_data = {"filename": filename}
    if file_url:
        insert_data["file_url"] = file_url
    doc_response = supabase.table("documents").insert(insert_data).execute()
    document_id = doc_response.data[0]["id"]

    # Step 3 — Extract and chunk text
    text = extract_text_from_pdf(file_bytes)
    num_pages = len(PyPDF2.PdfReader(io.BytesIO(file_bytes)).pages)
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    _progress(3, f"Creating chunks ({len(chunks)} chunks from {num_pages} pages)")

    # Step 4 — Generate embeddings
    _progress(4, "Generating embeddings")
    embeddings = embed_chunks(chunks)

    # Step 5 — Store in Supabase pgvector
    _progress(5, "Storing in pgvector")
    rows = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        rows.append({
            "document_id": document_id,
            "filename": filename,
            "content": chunk,
            "chunk_index": i,
            "embedding": embedding
        })

    # Insert in batches of 50 (Supabase limit)
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        supabase.table("chunks").insert(batch).execute()

    print(f"  Stored {len(rows)} chunks in pgvector")
    return {
        "filename": filename,
        "chunks": len(chunks),
        "pages": num_pages,
        "document_id": document_id
    }