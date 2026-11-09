from config import RETRIEVAL_COUNT, SIMILARITY_THRESHOLD
from database import supabase
from embeddings import get_embedder
from text_utils import display_name, format_context, visible_to  # format_context re-exported for app.py

# Ask the database for more candidates than we need, then keep only the ones this
# visitor may see (shared documents plus their own uploads).
CANDIDATE_COUNT = 200


def retrieve_relevant_chunks(query: str, session_id: str | None = None,
                             match_count: int = RETRIEVAL_COUNT) -> list[dict]:
    """
    Embed the query, find the most similar chunks in Supabase pgvector
    (cosine similarity above SIMILARITY_THRESHOLD), and return the top
    `match_count` that this session is allowed to see.
    """
    query_embedding = get_embedder().encode(query).tolist()

    results = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_count": CANDIDATE_COUNT,
        "match_threshold": SIMILARITY_THRESHOLD,
    }).execute()

    rows = [r for r in (results.data or []) if visible_to(r["filename"], session_id)][:match_count]
    for r in rows:
        r["filename"] = display_name(r["filename"])
    return rows  # list of {id, content, filename, chunk_index, similarity}
