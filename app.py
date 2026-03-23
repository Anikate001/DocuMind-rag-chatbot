import streamlit as st
import time
from ingest import ingest_pdf
from retriever import retrieve_relevant_chunks, format_context
from llm import answer_with_citations
from database import supabase

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DocuMind — RAG Chatbot",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []
if "questions_asked" not in st.session_state:
    st.session_state.questions_asked = 0
if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = []

# ─────────────────────────────────────────────
# CSS Injection
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── Hide Streamlit defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden !important;}
.stDeployButton {display: none;}

/* ── Root / body ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0A0A0A !important;
    color: #F0F0F0;
    font-family: 'Inter', sans-serif;
}
.main .block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

/* ── Custom Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #FF6B2B; border-radius: 2px; }

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #FF6B2B !important;
    color: #FF6B2B !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    padding: 6px 20px !important;
}
.stButton > button:hover {
    background: #FF6B2B !important;
    color: #0A0A0A !important;
    box-shadow: 0 0 20px rgba(255,107,43,0.4) !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: #1A1A1A !important;
    border: 1px dashed #2A2A2A !important;
    border-radius: 12px !important;
    transition: border-color 0.3s !important;
    padding: 10px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #FF6B2B !important;
}
[data-testid="stFileUploader"] label {
    color: #888 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stFileUploader"] button {
    background: transparent !important;
    border: 1px solid #FF6B2B !important;
    color: #FF6B2B !important;
    border-radius: 8px !important;
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 12px !important;
    margin: 8px 0 !important;
    padding: 12px 16px !important;
}
[data-testid="stChatMessage"][data-testid*="user"],
.stChatMessage:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 3px solid #FF6B2B !important;
}
[data-testid="stChatMessage"][data-testid*="assistant"],
.stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid #2ECC71 !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] {
    background: #1A1A1A !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 12px !important;
    color: #F0F0F0 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #FF6B2B !important;
    box-shadow: 0 0 0 3px rgba(255,107,43,0.15) !important;
}
[data-testid="stChatInput"] button {
    background: #FF6B2B !important;
    color: #0A0A0A !important;
    border-radius: 8px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D0D0D !important;
    border-right: 1px solid #1E1E1E !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: #F0F0F0;
}
[data-testid="stSidebar"] .stDivider {
    border-color: #1E1E1E !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #F0F0F0 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    color: #CCC !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 10px !important;
    padding: 12px !important;
}

/* ── Spinner override ── */
.stSpinner > div > div {
    border-top-color: #FF6B2B !important;
}

/* ── Select box, text input ── */
.stSelectbox > div > div, .stTextInput > div > div > input {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    color: #F0F0F0 !important;
    border-radius: 8px !important;
}
.stSelectbox > div > div:focus-within, .stTextInput > div > div > input:focus {
    border-color: #FF6B2B !important;
    box-shadow: 0 0 0 3px rgba(255,107,43,0.15) !important;
}

/* ─────────────── CUSTOM COMPONENT STYLES ─────────────── */

/* ── Header ── */
.app-header {
    position: relative;
    padding: 24px 0 16px;
    border-bottom: 1px solid #1E1E1E;
    margin-bottom: 24px;
}
.header-glow {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 300px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #FF6B2B, transparent);
    animation: slideGlow 3s ease-in-out infinite;
}
@keyframes slideGlow {
    0%, 100% { opacity: 0; transform: translateX(-200px); }
    50% { opacity: 1; transform: translateX(100px); }
}
.header-content {
    display: flex;
    align-items: center;
    gap: 16px;
}
.logo-icon {
    font-size: 2.2rem;
    color: #FF6B2B;
    animation: pulse 2s ease-in-out infinite;
    line-height: 1;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.header-text { flex: 1; }
.app-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #F0F0F0;
    margin: 0;
    line-height: 1.1;
}
.app-subtitle {
    color: #888;
    font-size: 0.85rem;
    margin: 4px 0 0;
    font-family: 'Inter', sans-serif;
}
.header-badge {
    margin-left: auto;
    background: #1A1A1A;
    border: 1px solid rgba(255,107,43,0.2);
    color: #FF6B2B;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-family: 'Space Grotesk', monospace;
    letter-spacing: 0.5px;
    white-space: nowrap;
}

/* ── Sidebar section label ── */
.sidebar-section-label {
    font-size: 0.65rem;
    letter-spacing: 2px;
    color: #FF6B2B;
    font-weight: 600;
    margin: 16px 0 8px;
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
}

/* ── Ingest success card ── */
.ingest-success {
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(135deg, #0D1F0D, #1A1A1A);
    border: 1px solid rgba(46,204,113,0.2);
    border-radius: 8px;
    padding: 10px 12px;
    margin: 4px 0;
    animation: fadeInUp 0.4s ease;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.success-icon {
    color: #2ECC71;
    font-size: 1.1rem;
    font-weight: 700;
    flex-shrink: 0;
}
.success-details { flex: 1; min-width: 0; }
.success-filename {
    color: #DDD;
    font-size: 0.82rem;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.success-stats {
    color: #666;
    font-size: 0.72rem;
    margin-top: 2px;
}

/* ── Document list items ── */
.doc-item {
    display: flex;
    align-items: center;
    padding: 8px 4px;
    border-bottom: 1px solid #1A1A1A;
    gap: 8px;
}
.doc-icon { color: #FF6B2B; font-size: 0.7rem; flex-shrink: 0; }
.doc-name {
    color: #CCC;
    font-size: 0.82rem;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.doc-date { color: #444; font-size: 0.72rem; white-space: nowrap; }

/* ── Stats bar ── */
.stat-item {
    text-align: center;
    padding: 14px 8px;
    background: #111;
    border: 1px solid #1E1E1E;
    border-radius: 10px;
}
.stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #FF6B2B;
    font-family: 'Space Grotesk', sans-serif;
    line-height: 1.2;
}
.stat-label {
    font-size: 0.7rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
    font-family: 'Inter', sans-serif;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
}
.empty-icon {
    font-size: 3rem;
    color: #FF6B2B;
    animation: pulse 2s ease-in-out infinite;
    margin-bottom: 16px;
    display: inline-block;
}
.empty-title {
    color: #F0F0F0;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 600;
    margin: 0 0 8px;
}
.empty-subtitle {
    color: #666;
    font-size: 0.9rem;
    margin: 0;
}
.suggestion-chips {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 20px;
}
.chip {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    color: #888;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.8rem;
    cursor: default;
    transition: all 0.2s;
    font-family: 'Inter', sans-serif;
}
.chip:hover {
    border-color: #FF6B2B;
    color: #FF6B2B;
}

/* ── Chunk cards ── */
.chunk-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 12px;
    margin: 6px 0;
    transition: all 0.2s;
    cursor: default;
}
.chunk-card:hover {
    border-color: rgba(255,107,43,0.2);
    transform: translateY(-1px);
}
.chunk-header {
    display: flex;
    align-items: center;
    gap: 6px;
}
.chunk-rank {
    color: #FF6B2B;
    font-weight: 700;
    font-family: 'Space Grotesk', monospace;
    font-size: 0.8rem;
    flex-shrink: 0;
}
.chunk-file {
    color: #888;
    font-size: 0.78rem;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.sim-high { color: #2ECC71; font-size: 0.75rem; font-weight: 600; }
.sim-mid  { color: #F39C12; font-size: 0.75rem; font-weight: 600; }
.sim-low  { color: #888;    font-size: 0.75rem; font-weight: 600; }
.chunk-preview {
    color: #666;
    font-size: 0.78rem;
    line-height: 1.5;
    margin: 8px 0;
    border-left: 2px solid #2A2A2A;
    padding-left: 8px;
}
.chunk-footer {
    color: #333;
    font-size: 0.7rem;
}

/* ── Processing card ── */
.processing-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}
.proc-title {
    color: #F0F0F0;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 12px;
}
.proc-step {
    color: #444;
    font-size: 0.8rem;
    padding: 4px 0;
    font-family: 'Inter', sans-serif;
    transition: color 0.3s;
}
.proc-step.active {
    color: #FF6B2B;
    animation: pulse 1.2s ease-in-out infinite;
}
.proc-step.done {
    color: #2ECC71;
}

/* ── Right panel section heading ── */
.panel-heading {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: #F0F0F0;
    margin-bottom: 4px;
}
.panel-caption {
    font-size: 0.75rem;
    color: #555;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Animated Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="header-glow"></div>
    <div class="header-content">
        <div class="logo-icon">◈</div>
        <div class="header-text">
            <h1 class="app-title">DocuMind</h1>
            <p class="app-subtitle">Upload documents · Ask questions · Get cited answers</p>
        </div>
        <div class="header-badge">RAG · Llama3 · pgvector</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helper: Fetch live stats
# ─────────────────────────────────────────────
@st.cache_data(ttl=10)
def get_stats():
    try:
        docs = supabase.table("documents").select("id", count="exact").execute()
        chunks = supabase.table("chunks").select("id", count="exact").execute()
        return docs.count or 0, chunks.count or 0
    except Exception:
        return 0, 0

doc_count, chunk_count = get_stats()

# ─────────────────────────────────────────────
# Stats Bar
# ─────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(f"""<div class="stat-item"><div class="stat-value">{doc_count}</div><div class="stat-label">Documents</div></div>""", unsafe_allow_html=True)
with s2:
    st.markdown(f"""<div class="stat-item"><div class="stat-value">{chunk_count}</div><div class="stat-label">Total Chunks</div></div>""", unsafe_allow_html=True)
with s3:
    st.markdown(f"""<div class="stat-item"><div class="stat-value">{st.session_state.questions_asked}</div><div class="stat-label">Questions Asked</div></div>""", unsafe_allow_html=True)
with s4:
    st.markdown("""<div class="stat-item"><div class="stat-value">Llama3</div><div class="stat-label">LLM Model</div></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar — PDF Upload
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-section-label">📁 DOCUMENTS</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.ingested_files:
                # Processing animation placeholder
                progress_placeholder = st.empty()
                # Use a mutable list to avoid nonlocal issues
                steps_state_container = [["pending"] * 5]
                step_labels = [
                    "Uploading to storage",
                    "Extracting text",
                    "Creating chunks",
                    "Generating embeddings",
                    "Storing in pgvector"
                ]

                def render_processing(filename, current_steps, labels):
                    steps_html = ""
                    for idx, (state, label) in enumerate(zip(current_steps, labels)):
                        if state == "done":
                            steps_html += f'<div class="proc-step done">✓ {label}</div>'
                        elif state == "active":
                            steps_html += f'<div class="proc-step active">◈ {label}</div>'
                        else:
                            steps_html += f'<div class="proc-step">◈ {label}</div>'
                    return f"""
                    <div class="processing-card">
                        <div class="proc-title">Processing {filename}</div>
                        <div class="proc-steps">{steps_html}</div>
                    </div>"""

                def on_progress(step, msg):
                    ss = steps_state_container[0]
                    # Mark previous steps done
                    for i in range(step):
                        if i < len(ss):
                            ss[i] = "done"
                    if step < len(ss):
                        ss[step] = "active"
                    progress_placeholder.markdown(
                        render_processing(uploaded_file.name, ss, step_labels),
                        unsafe_allow_html=True
                    )

                on_progress(0, "Starting")
                try:
                    result = ingest_pdf(
                        uploaded_file.read(),
                        uploaded_file.name,
                        progress_callback=on_progress
                    )
                    # Mark all done
                    steps_state_container[0] = ["done"] * 5
                    progress_placeholder.markdown(
                        render_processing(uploaded_file.name, steps_state_container[0], step_labels),
                        unsafe_allow_html=True
                    )
                    time.sleep(0.5)
                    progress_placeholder.empty()

                    st.session_state.ingested_files.append(uploaded_file.name)

                    # Show success card
                    pages = result.get("pages", "?")
                    chunks = result.get("chunks", "?")
                    st.markdown(f"""
                    <div class="ingest-success">
                        <div class="success-icon">✓</div>
                        <div class="success-details">
                            <div class="success-filename">{uploaded_file.name}</div>
                            <div class="success-stats">{pages} pages · {chunks} chunks · indexed</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    st.cache_data.clear()
                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"Error: {str(e)}")

    # Show ingested files this session
    if st.session_state.ingested_files:
        for fname in st.session_state.ingested_files:
            st.markdown(f"""
            <div class="ingest-success">
                <div class="success-icon">✓</div>
                <div class="success-details">
                    <div class="success-filename">{fname}</div>
                    <div class="success-stats">indexed this session</div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # All Documents in DB
    st.markdown('<div class="sidebar-section-label">📚 ALL DOCUMENTS IN DB</div>', unsafe_allow_html=True)
    try:
        docs = supabase.table("documents").select("filename, uploaded_at").order("uploaded_at", desc=True).execute()
        if docs.data:
            for doc in docs.data:
                date_str = doc.get("uploaded_at", "")[:10] if doc.get("uploaded_at") else ""
                st.markdown(f"""
                <div class="doc-item">
                    <span class="doc-icon">◈</span>
                    <span class="doc-name">{doc['filename']}</span>
                    <span class="doc-date">{date_str}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#444; font-size:0.8rem;">No documents uploaded yet</p>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<p style="color:#444; font-size:0.8rem;">No documents yet</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main Chat + Chunks Panel
# ─────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    # Display chat history
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">◈</div>
            <h3 class="empty-title">Ready to explore your documents</h3>
            <p class="empty-subtitle">Upload a PDF in the sidebar, then ask anything about it.</p>
            <div class="suggestion-chips">
                <div class="chip">Summarize this document</div>
                <div class="chip">What are the key findings?</div>
                <div class="chip">List all recommendations</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Increment questions counter
        st.session_state.questions_asked += 1

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate answer
        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                try:
                    # Retrieve relevant chunks
                    chunks = retrieve_relevant_chunks(prompt, match_count=5)
                    st.session_state.last_chunks = chunks

                    if not chunks:
                        answer = "I couldn't find relevant information in the uploaded documents. Please upload a PDF first or try a different question."
                    else:
                        # Format context with citations
                        context, citations = format_context(chunks)
                        # Get LLM answer
                        answer = answer_with_citations(prompt, context, citations)

                    # Typing animation — stream character by character
                    answer_placeholder = st.empty()
                    displayed = ""
                    for char in answer:
                        displayed += char
                        answer_placeholder.markdown(displayed + "▌")
                        time.sleep(0.008)
                    answer_placeholder.markdown(displayed)

                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"Error: {str(e)}")

with col2:
    st.markdown('<div class="panel-heading">🔍 Retrieved Chunks</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-caption">What the model actually looked at</div>', unsafe_allow_html=True)

    chunks_to_show = st.session_state.last_chunks

    if chunks_to_show:
        for i, chunk in enumerate(chunks_to_show[:5]):
            sim = chunk.get("similarity", 0)
            if sim > 0.7:
                sim_class = "sim-high"
            elif sim > 0.5:
                sim_class = "sim-mid"
            else:
                sim_class = "sim-low"

            content_preview = chunk.get("content", "")[:200].replace("<", "&lt;").replace(">", "&gt;")
            fname = chunk.get("filename", "unknown")
            cidx = chunk.get("chunk_index", 0)

            st.markdown(f"""
            <div class="chunk-card">
                <div class="chunk-header">
                    <span class="chunk-rank">[{i+1}]</span>
                    <span class="chunk-file">{fname}</span>
                    <span class="{sim_class}">{sim:.0%}</span>
                </div>
                <div class="chunk-preview">{content_preview}...</div>
                <div class="chunk-footer">chunk #{cidx + 1}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#444; font-size:0.8rem; text-align:center; margin-top:24px;">Ask a question to see retrieved chunks here</p>', unsafe_allow_html=True)