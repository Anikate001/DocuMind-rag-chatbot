# 📄 DocuMind — RAG Chatbot

> **A production-grade Retrieval-Augmented Generation (RAG) chatbot.**  
> Upload PDF documents, ask questions in natural language, and get cited answers — eliminating hallucination by design.

![DocuMind Screenshot](https://img.shields.io/badge/Status-Live-2ECC71?style=flat-square) ![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?style=flat-square&logo=supabase&logoColor=white) ![Groq](https://img.shields.io/badge/Groq-Llama3--70B-FF6B2B?style=flat-square)

---

## 🎯 What It Does

DocuMind lets you **upload PDF documents** and **ask questions** about their content. Every answer includes **citations** pointing to the exact source chunk — so you always know where the information came from.

**Example workflow:**
1. Upload a 50-page research paper
2. Ask: *"What are the key findings of this study?"*
3. Get a precise, cited answer referencing specific sections of the paper

---

## 🏗️ Architecture & Methods

```
┌─────────────────────────────────────────────────────────────┐
│                    DocuMind RAG Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📄 PDF Upload                                              │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │  Extract Text │──▶│ Chunk Text   │──▶│  Embed with  │    │
│  │  (PyPDF2)     │   │ (500 words,  │   │  MiniLM-L6   │    │
│  │               │   │  50 overlap) │   │  (384-dim)   │    │
│  └──────────────┘   └──────────────┘   └──────┬───────┘    │
│                                                │            │
│                                         ┌──────▼───────┐    │
│                                         │  Store in    │    │
│                                         │  Supabase    │    │
│                                         │  pgvector    │    │
│                                         └──────────────┘    │
│                                                             │
│  ❓ User Query                                              │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ Embed Query   │──▶│ Cosine       │──▶│ Send Top-5   │    │
│  │ (same model)  │   │ Similarity   │   │ Chunks + Q   │    │
│  │               │   │ Search       │   │ to Groq LLM  │    │
│  └──────────────┘   └──────────────┘   └──────┬───────┘    │
│                                                │            │
│                                     ┌──────────▼─────────┐  │
│                                     │  Cited Answer      │  │
│                                     │  with [1],[2],[3]  │  │
│                                     │  source references │  │
│                                     └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Methods Used

| Component | Method / Technology | Why This Choice |
|-----------|-------------------|-----------------|
| **Text Extraction** | PyPDF2 | Extracts text from PDF pages without external APIs |
| **Chunking** | Sliding window (500 words, 50 overlap) | Overlap ensures answers spanning chunk boundaries are still retrievable |
| **Embeddings** | `all-MiniLM-L6-v2` (HuggingFace) | Free, local, 384-dim vectors — no API cost, runs on CPU |
| **Vector Database** | Supabase pgvector | Free PostgreSQL with vector similarity search built-in |
| **Similarity Search** | Cosine similarity via `match_chunks` RPC | Finds the most semantically relevant chunks for any query |
| **LLM** | Groq `llama-3.3-70b-versatile` | Free tier (14,400 req/day), fastest inference available |
| **Prompt Engineering** | System prompt with citation rules | Forces the model to cite sources [1],[2] and never hallucinate |
| **Frontend** | Streamlit with custom CSS injection | Premium dark UI with typing animations, no JavaScript needed |

### Key Design Decisions

- **Temperature = 0.1** → Low temperature produces factual, deterministic answers and reduces hallucination
- **Top-5 retrieval** → Balances context richness with token limits
- **Similarity threshold = 0.3** → Filters out irrelevant chunks without being too aggressive
- **Same embedding model** for both ingestion and retrieval → Critical for consistent vector space matching
- **Overlapping chunks** → Prevents information loss at chunk boundaries

---

## 🛠️ Tech Stack (100% Free)

| Service | Purpose | Cost |
|---------|---------|------|
| **Supabase** | PostgreSQL + pgvector + Storage | Free tier |
| **Groq** | LLM inference (Llama3-70B) | Free (14,400 req/day) |
| **HuggingFace** | Sentence-transformer embeddings | Free (runs locally) |
| **Streamlit** | Frontend + hosting | Free |

---

## 📁 Project Structure

```
rag-chatbot/
├── app.py              # Streamlit UI — premium dark theme with animations
├── config.py           # Environment variable loader
├── database.py         # Supabase client (single shared instance)
├── ingest.py           # PDF → text → chunks → embeddings → pgvector
├── retriever.py        # Query embedding + cosine similarity search
├── llm.py              # Groq Llama3 answer generation with citations
├── requirements.txt    # Python dependencies
├── .env.example        # Template for environment variables
├── .streamlit/
│   └── config.toml     # Streamlit dark theme configuration
└── README.md           # This file
```

---

## 🗄️ How Supabase Is Used

Supabase serves as the **complete backend** for this project — database, vector search, and file storage.

### Database Tables

**`documents` table** — stores metadata for each uploaded PDF:
```sql
CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_url    TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
```

**`chunks` table** — stores text chunks with their vector embeddings:
```sql
CREATE TABLE chunks (
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    filename    TEXT,
    content     TEXT NOT NULL,
    chunk_index INT,
    embedding   VECTOR(384),
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### Vector Search Function

The `match_chunks` RPC function performs cosine similarity search directly in PostgreSQL:
```sql
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(384),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    filename TEXT,
    chunk_index INT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        chunks.id,
        chunks.content,
        chunks.filename,
        chunks.chunk_index,
        1 - (chunks.embedding <=> query_embedding) AS similarity
    FROM chunks
    WHERE 1 - (chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### Supabase Storage

Raw PDF files are uploaded to a public **Storage bucket** (`documents`) so users can reference the original files. The bucket is auto-created on first upload via the REST API.

### Setup Steps in Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Enable the **pgvector extension**: SQL Editor → `CREATE EXTENSION IF NOT EXISTS vector;`
3. Create the `documents` and `chunks` tables (SQL above)
4. Create the `match_chunks` function (SQL above)
5. Copy your **Project URL** and **service_role key** from Settings → API

---

## 🚀 How to Run

### Prerequisites
- Python 3.11+
- Supabase account with pgvector enabled
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone the Repository
```bash
git clone https://github.com/Anikate001/rag-chatbot.git
cd rag-chatbot
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env and fill in your keys
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Supabase
- Enable pgvector: `CREATE EXTENSION IF NOT EXISTS vector;`
- Run the SQL statements from the [Supabase section](#-how-supabase-is-used) to create tables and the `match_chunks` function

### 5. Run the App
```bash
streamlit run app.py
# Open http://localhost:8501
```

### 6. Use It
1. Upload a PDF via the sidebar
2. Wait for processing (extraction → chunking → embedding → storage)
3. Ask questions in the chat input
4. Get cited answers with source references!

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Service role key (from Settings → API) |
| `GROQ_API_KEY` | ✅ | From [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | ❌ | Default: `llama-3.3-70b-versatile` |
| `EMBEDDING_MODEL` | ❌ | Default: `all-MiniLM-L6-v2` |
| `RETRIEVAL_COUNT` | ❌ | Default: `5` chunks per query |
| `SIMILARITY_THRESHOLD` | ❌ | Default: `0.3` (range 0.0–1.0) |
| `MAX_RESPONSE_TOKENS` | ❌ | Default: `1024` |

---

## ⚡ Challenges Faced & Solutions

### 1. API Key Permissions (RLS)
**Challenge:** The Supabase `publishable` (anon) key was blocked by **Row Level Security (RLS)** — all database INSERTs and Storage operations returned `401 Unauthorized`.  
**Solution:** Switched to the `service_role` key which bypasses RLS entirely. For production, proper RLS policies should be configured instead.

### 2. Storage Bucket Creation
**Challenge:** The Python Supabase SDK's `create_bucket()` method had parameter signature mismatches that caused `400 Bad Request` errors.  
**Solution:** Replaced the SDK call with a direct **REST API request** (`POST /storage/v1/bucket`) which works reliably. The bucket is auto-created if it doesn't exist.

### 3. Deprecated LLM Model
**Challenge:** The original `llama3-70b-8192` model was decommissioned by Groq, causing all LLM calls to fail.  
**Solution:** Listed available models via the Groq API and switched to `llama-3.3-70b-versatile`, which is currently active and free.

### 4. Embedding Model Download Latency
**Challenge:** The `all-MiniLM-L6-v2` model (~90MB) downloads on first use, causing the app to appear frozen.  
**Solution:** The model is loaded once at module import time and cached. After the initial download, subsequent runs start instantly.

### 5. Chunk Boundary Information Loss
**Challenge:** Naive text splitting can cut sentences mid-thought, making chunks lose context.  
**Solution:** Implemented **overlapping chunks** (500 words with 50-word overlap), ensuring that information spanning chunk boundaries is captured in at least one chunk.

### 6. Streamlit UI Limitations
**Challenge:** Streamlit doesn't support custom JavaScript, making it hard to create premium interactive UIs.  
**Solution:** Used **CSS injection via `st.markdown(unsafe_allow_html=True)`** to override all default Streamlit styles, add animations (`@keyframes`), custom scrollbars, and a complete dark theme — all without JavaScript.

---

## 🎨 UI Features

- **Dark theme** with `#0A0A0A` background and `#FF6B2B` warm orange accent
- **Animated header** with glowing accent line and pulsing logo
- **Real-time stats bar** — Documents, Chunks, Questions Asked, Model
- **Processing cards** — step-by-step progress during PDF ingestion
- **Typing animation** — assistant responses stream character-by-character
- **Chunk cards** — color-coded similarity scores (green/yellow/grey)
- **Suggestion chips** — quick-start prompts for new users

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [Supabase](https://supabase.com) — for the free PostgreSQL + pgvector platform
- [Groq](https://groq.com) — for the fastest free LLM inference
- [HuggingFace](https://huggingface.co) — for the `all-MiniLM-L6-v2` embedding model
- [Streamlit](https://streamlit.io) — for the Python web framework

---

*Built by [Anikate001](https://github.com/Anikate001)*
