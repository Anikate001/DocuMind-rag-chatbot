from sentence_transformers import SentenceTransformer
from database import supabase
from text_utils import format_context  # re-exported for app.py

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

