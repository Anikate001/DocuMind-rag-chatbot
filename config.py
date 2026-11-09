import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq retired the Llama 3.x models on 16 Aug 2026; gpt-oss-120b is its recommended replacement
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RETRIEVAL_COUNT = int(os.getenv("RETRIEVAL_COUNT", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
# 100-word chunks won the eval (recall@5 93% vs 57% for 500-word chunks); see eval/README.md
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "100"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "10"))
MAX_RESPONSE_TOKENS = int(os.getenv("MAX_RESPONSE_TOKENS", "1024"))
# Larger PDFs can exhaust the 1 GB free Streamlit Cloud instance
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
