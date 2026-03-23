from sentence_transformers import SentenceTransformer
from database import supabase

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_relevant_chunks(query: str, match_count: int = 5) -> list[dict]:
    """
    Embed the query then find the most similar chunks
    in Supabase pgvector using cosine similarity.
    """
    # Embed the query
    query_embedding = embedder.encode(query).tolist()

    # Call our SQL function
    results = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_count": match_count,
        "match_threshold": 0.3
    }).execute()

    return results.data  # list of {id, content, filename, chunk_index, similarity}

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