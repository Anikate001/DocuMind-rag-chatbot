import streamlit as st

from retro_ui import arcade_hero, energy_can_egg, inject_theme, pixel_svg, xp_bar
import re
import threading
import time
import uuid
from config import MAX_UPLOAD_MB
from ingest import ingest_pdf
from retriever import retrieve_relevant_chunks, format_context
from llm import answer_with_citations
from embeddings import get_embedder
from database import supabase
from text_utils import display_name, visible_to

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DocuMind — RAG Chatbot",
    page_icon="🕹️",
    layout="wide",
    initial_sidebar_state="auto"
)

@st.cache_resource(show_spinner=False)
def _warm_embedder():
    """Load the embedding model in the background so the first question isn't slow."""
    threading.Thread(target=get_embedder, daemon=True, name="warm-embedder").start()
    return True


_warm_embedder()

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
if "session_id" not in st.session_state:
    # Scopes this visitor's uploads so other visitors never see them
    st.session_state.session_id = uuid.uuid4().hex[:8]

# Count a question on the run it is submitted, before the stats bar is drawn
if st.session_state.get("chat_q"):
    st.session_state.questions_asked += 1

SUGGESTIONS = ["Summarize this document", "What are the key findings?", "List all recommendations"]


def _ask(question):
    """Suggestion chips ask their question as if it were typed."""
    st.session_state.pending_q = question
    st.session_state.questions_asked += 1

# ─────────────────────────────────────────────
# CSS Injection
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */


/* ── Hide Streamlit defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent !important;}
/* the header holds the button that reopens the sidebar, so it must stay visible */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {visibility: visible !important; display: flex !important;}
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], .stAppDeployButton {display: none !important;}
.stDeployButton {display: none;}

/* ── Root / body ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0B0420 !important;
    color: #F2E9FF;
    font-family: 'VT323', monospace;
}
.main .block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

/* ── Custom Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #05020F; }
::-webkit-scrollbar-thumb { background: #FF2E97; border-radius: 0; }

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #FF2E97 !important;
    color: #FF2E97 !important;
    border-radius: 0 !important;
    font-family: 'VT323', monospace !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    padding: 6px 20px !important;
}
.stButton > button:hover {
    background: #FF2E97 !important;
    color: #0B0420 !important;
    box-shadow: 0 0 20px rgba(255,46,151,0.4) !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: #160A33 !important;
    border: 1px dashed #2A1650 !important;
    border-radius: 0 !important;
    transition: border-color 0.3s !important;
    padding: 10px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #FF2E97 !important;
}
[data-testid="stFileUploader"] label {
    color: #C9BEE8 !important;
    font-family: 'VT323', monospace !important;
}
[data-testid="stFileUploader"] button {
    background: transparent !important;
    border: 1px solid #FF2E97 !important;
    color: #FF2E97 !important;
    border-radius: 0 !important;
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: #160A33 !important;
    border: 1px solid #2A1650 !important;
    border-radius: 0 !important;
    margin: 8px 0 !important;
    padding: 12px 16px !important;
}
[data-testid="stChatMessage"][data-testid*="user"],
.stChatMessage:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 3px solid #FF2E97 !important;
}
[data-testid="stChatMessage"][data-testid*="assistant"],
.stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid #39FF14 !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] {
    background: #160A33 !important;
    border-radius: 0 !important;
}
[data-testid="stChatInput"] textarea {
    background: #160A33 !important;
    border: 1px solid #2A1650 !important;
    border-radius: 0 !important;
    color: #F2E9FF !important;
    font-family: 'VT323', monospace !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #FF2E97 !important;
    box-shadow: 0 0 0 3px rgba(255,46,151,0.15) !important;
}
[data-testid="stChatInput"] button {
    background: #FF2E97 !important;
    color: #0B0420 !important;
    border-radius: 0 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0B0420 !important;
    border-right: 1px solid #1C0D40 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: #F2E9FF;
}
[data-testid="stSidebar"] .stDivider {
    border-color: #1C0D40 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #160A33 !important;
    border: 1px solid #2A1650 !important;
    border-radius: 0 !important;
}
[data-testid="stExpander"] summary {
    color: #F2E9FF !important;
    font-family: 'VT323', monospace !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    color: #CCC !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #160A33 !important;
    border: 1px solid #2A1650 !important;
    border-radius: 0 !important;
    padding: 12px !important;
}

/* ── Spinner override ── */
.stSpinner > div > div {
    border-top-color: #FF2E97 !important;
}

/* ── Select box, text input ── */
.stSelectbox > div > div, .stTextInput > div > div > input {
    background: #160A33 !important;
    border: 1px solid #2A1650 !important;
    color: #F2E9FF !important;
    border-radius: 0 !important;
}
.stSelectbox > div > div:focus-within, .stTextInput > div > div > input:focus {
    border-color: #FF2E97 !important;
    box-shadow: 0 0 0 3px rgba(255,46,151,0.15) !important;
}

/* ─────────────── CUSTOM COMPONENT STYLES ─────────────── */

/* ── Header ── */
.app-header {
    position: relative;
    padding: 24px 0 16px;
    border-bottom: 1px solid #1C0D40;
    margin-bottom: 24px;
}
.header-glow {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 300px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #FF2E97, transparent);
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
    color: #FF2E97;
    animation: pulse 2s ease-in-out infinite;
    line-height: 1;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.header-text { flex: 1; }
.app-title {
    font-family: 'Press Start 2P', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #F2E9FF;
    margin: 0;
    line-height: 1.1;
}
.app-subtitle {
    color: #C9BEE8;
    font-size: 0.85rem;
    margin: 4px 0 0;
    font-family: 'VT323', monospace;
}
.header-badge {
    margin-left: auto;
    background: #160A33;
    border: 1px solid rgba(255,46,151,0.2);
    color: #FF2E97;
    padding: 4px 14px;
    border-radius: 0;
    font-size: 0.75rem;
    font-family: 'Press Start 2P', monospace;
    letter-spacing: 0.5px;
    white-space: nowrap;
}

/* ── Sidebar section label ── */
.sidebar-section-label {
    font-size: 0.65rem;
    letter-spacing: 2px;
    color: #FF2E97;
    font-weight: 600;
    margin: 16px 0 8px;
    font-family: 'VT323', monospace;
    text-transform: uppercase;
}

/* ── Ingest success card ── */
.ingest-success {
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(135deg, #0B2A12, #160A33);
    border: 1px solid rgba(57,255,20,0.2);
    border-radius: 0;
    padding: 10px 12px;
    margin: 4px 0;
    animation: fadeInUp 0.4s ease;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.success-icon {
    color: #39FF14;
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
    color: #B8ADD6;
    font-size: 0.72rem;
    margin-top: 2px;
}

/* ── Document list items ── */
.doc-item {
    display: flex;
    align-items: center;
    padding: 8px 4px;
    border-bottom: 1px solid #160A33;
    gap: 8px;
}
.doc-icon { color: #FF2E97; font-size: 0.7rem; flex-shrink: 0; }
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
    background: #05020F;
    border: 1px solid #1C0D40;
    border-radius: 0;
}
.stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #FF2E97;
    font-family: 'Press Start 2P', monospace;
    line-height: 1.2;
}
.stat-label {
    font-size: 0.7rem;
    color: #9A8FBF;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
    font-family: 'VT323', monospace;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
}
.empty-icon {
    font-size: 3rem;
    color: #FF2E97;
    animation: pulse 2s ease-in-out infinite;
    margin-bottom: 16px;
    display: inline-block;
}
.empty-title {
    color: #F2E9FF;
    font-family: 'Press Start 2P', monospace;
    font-size: 1.3rem;
    font-weight: 600;
    margin: 0 0 8px;
}
.empty-subtitle {
    color: #B8ADD6;
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
    background: #160A33;
    border: 1px solid #2A1650;
    color: #C9BEE8;
    padding: 8px 16px;
    border-radius: 0;
    font-size: 0.8rem;
    cursor: default;
    transition: all 0.2s;
    font-family: 'VT323', monospace;
}
.chip:hover {
    border-color: #FF2E97;
    color: #FF2E97;
}

/* ── Chunk cards ── */
.chunk-card {
    background: #05020F;
    border: none;
    border-radius: 0;
    padding: 12px;
    margin: 6px 0;
    transition: all 0.2s;
    cursor: default;
}
.chunk-card:hover {
    border-color: rgba(255,46,151,0.2);
    transform: translateY(-1px);
}
.chunk-header {
    display: flex;
    align-items: center;
    gap: 6px;
}
.chunk-rank {
    color: #FF2E97;
    font-weight: 700;
    font-family: 'Press Start 2P', monospace;
    font-size: 0.8rem;
    flex-shrink: 0;
}
.chunk-file {
    color: #C9BEE8;
    font-size: 0.78rem;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.sim-high { color: #39FF14; font-size: 0.75rem; font-weight: 600; }
.sim-mid  { color: #FFE600; font-size: 0.75rem; font-weight: 600; }
.sim-low  { color: #B8ADD6;    font-size: 0.75rem; font-weight: 600; }
.chunk-preview {
    color: #B8ADD6;
    font-size: 0.78rem;
    line-height: 1.5;
    margin: 8px 0;
    border-left: 2px solid #2A1650;
    padding-left: 8px;
}
.chunk-footer {
    color: #9A8FBF;
    font-size: 0.7rem;
}

/* ── Processing card ── */
.processing-card {
    background: #05020F;
    border: none;
    border-radius: 0;
    padding: 16px;
    margin: 8px 0;
}
.proc-title {
    color: #F2E9FF;
    font-family: 'Press Start 2P', monospace;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 12px;
}
.proc-step {
    color: #444;
    font-size: 0.8rem;
    padding: 4px 0;
    font-family: 'VT323', monospace;
    transition: color 0.3s;
}
.proc-step.active {
    color: #FF2E97;
    animation: pulse 1.2s ease-in-out infinite;
}
.proc-step.done {
    color: #39FF14;
}

/* ── Right panel section heading ── */
.panel-heading {
    font-family: 'Press Start 2P', monospace;
    font-size: 0.9rem;
    font-weight: 600;
    color: #F2E9FF;
    margin-bottom: 4px;
}
.panel-caption {
    font-size: 0.75rem;
    color: #9A8FBF;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# Retro arcade theme: loads after the base CSS so it wins.
inject_theme()

# ─────────────────────────────────────────────
# Animated Header
# ─────────────────────────────────────────────
arcade_hero(
    title="DOCUMIND",
    subtitle="RAG DOCUMENT QUEST",
    tagline="Feed it your PDFs, ask anything, and get answers with citations. "
            "If the answer isn't in your documents, it tells you.",
    status_html='<span class="hud-chip">RAG &middot; GPT-OSS &middot; PGVECTOR</span>',
    stickers=("cabinet", "coin", "heart", "cat", "star"),
)

# ─────────────────────────────────────────────
# Helper: Fetch live stats
# ─────────────────────────────────────────────
@st.cache_data(ttl=10)
def get_visible_documents(session_id):
    """Shared documents plus this session's uploads, newest first."""
    try:
        docs = supabase.table("documents").select("filename, uploaded_at").order("uploaded_at", desc=True).execute()
        return [d for d in (docs.data or []) if visible_to(d["filename"], session_id)]
    except Exception:
        return []


@st.cache_data(ttl=10)
def get_chunk_count(filenames):
    if not filenames:
        return 0
    try:
        res = supabase.table("chunks").select("id", count="exact").in_("filename", list(filenames)).execute()
        return res.count or 0
    except Exception:
        return 0


visible_docs = get_visible_documents(st.session_state.session_id)
doc_count = len(visible_docs)
chunk_count = get_chunk_count(tuple(d["filename"] for d in visible_docs))

# ─────────────────────────────────────────────
# Stats Bar
# ─────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(f"""<div class="stat-item"><div class="stat-value">{doc_count}</div><div class="stat-label">Docs Loaded</div></div>""", unsafe_allow_html=True)
with s2:
    st.markdown(f"""<div class="stat-item"><div class="stat-value">{chunk_count}</div><div class="stat-label">Chunks</div></div>""", unsafe_allow_html=True)
with s3:
    st.markdown(f"""<div class="stat-item"><div class="stat-value">{st.session_state.questions_asked}</div><div class="stat-label">Score</div></div>""", unsafe_allow_html=True)
with s4:
    st.markdown("""<div class="stat-item"><div class="stat-value">gpt-oss</div><div class="stat-label">Engine</div></div>""", unsafe_allow_html=True)

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
            if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
                st.warning(f"{uploaded_file.name} is over {MAX_UPLOAD_MB} MB, so it was skipped.")
                continue
            if uploaded_file.name not in st.session_state.ingested_files:
                # Processing animation placeholder
                progress_placeholder = st.empty()
                # Use a mutable list to avoid nonlocal issues
                steps_state_container = [["pending"] * 5]
                step_labels = [
                    "Reading PDF",
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
                        progress_callback=on_progress,
                        session_id=st.session_state.session_id,
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
    st.markdown('<div class="sidebar-section-label">📚 DOCUMENTS YOU CAN SEARCH</div>', unsafe_allow_html=True)
    if visible_docs:
        for doc in visible_docs:
            date_str = doc.get("uploaded_at", "")[:10] if doc.get("uploaded_at") else ""
            mine = display_name(doc["filename"]) != doc["filename"]
            label = "yours" if mine else "sample"
            st.markdown(f"""
            <div class="doc-item">
                <span class="doc-icon">◈</span>
                <span class="doc-name">{display_name(doc['filename'])}</span>
                <span class="doc-date">{label} · {date_str}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#B8ADD6; font-size:0.8rem;">No documents yet</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#B8ADD6; font-size:0.72rem; margin-top:8px;">Your uploads are only visible in this browser session. Please don\'t upload confidential documents to this public demo.</p>', unsafe_allow_html=True)
    energy_can_egg(st)

# ─────────────────────────────────────────────
# Main Chat + Chunks Panel
# ─────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    # Intro card, cleared as soon as the first question is asked
    intro = st.empty()
    if not st.session_state.messages:
        intro_box = intro.container()
        intro_box.markdown("""
        <div class="empty-state">
            <div class="empty-icon">{cab}</div>
            <h3 class="empty-title">Ready to explore your documents</h3>
            <p class="empty-subtitle">Ask about the sample AquaPilot X3 manual, or upload your own PDF in the sidebar.</p>
        </div>
        """.replace("{cab}", pixel_svg("cabinet", 7, "Arcade cabinet")), unsafe_allow_html=True)
        chip_cols = intro_box.columns(len(SUGGESTIONS))
        for col, q in zip(chip_cols, SUGGESTIONS):
            col.button(q, key=f"chip_{q}", on_click=_ask, args=(q,), use_container_width=True)
    # Messages go in a container placed above the input, so new answers appear
    # above the chat box instead of below it
    history = st.container()
    with history:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input (the questions counter is updated at the top of the script)
    typed = st.chat_input("Ask a question about your documents...", key="chat_q")
    if prompt := (typed or st.session_state.pop("pending_q", None)):
        intro.empty()
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with history, st.chat_message("user"):
            st.markdown(prompt)

        # Generate answer
        with history, st.chat_message("assistant"):
            with st.spinner("Scanning documents..."):
                try:
                    # Retrieve relevant chunks
                    chunks = retrieve_relevant_chunks(prompt, session_id=st.session_state.session_id)
                    st.session_state.last_chunks = chunks

                    if not chunks:
                        answer = "I couldn't find relevant information in the uploaded documents. Please upload a PDF first or try a different question."
                    else:
                        # Format context with citations
                        context, citations = format_context(chunks)
                        # Get LLM answer
                        answer = answer_with_citations(prompt, context, citations)

                    # Typing effect, streamed word by word (one update per word, not per character)
                    def _words(text):
                        for token in re.split(r"(\s+)", text):
                            yield token
                            if token.strip():
                                time.sleep(0.015)

                    st.write_stream(_words(answer))

                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"Error: {str(e)}")

with col2:
    st.markdown('<div class="panel-heading">&#9654; RETRIEVED CHUNKS</div>', unsafe_allow_html=True)
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

            raw = chunk.get("content", "")
            content_preview = raw[:200].replace("<", "&lt;").replace(">", "&gt;")
            if len(raw) > 200:
                content_preview = content_preview.rstrip(" .") + "&hellip;"
            fname = chunk.get("filename", "unknown")
            cidx = chunk.get("chunk_index", 0)

            st.markdown(f"""
            <div class="chunk-card">
                <div class="chunk-header">
                    <span class="chunk-rank">#{i+1}</span>
                    <span class="chunk-file">{fname}</span>
                    <span class="{sim_class}">{sim:.0%}</span>
                </div>
                <div class="chunk-preview">{content_preview}</div>
                {xp_bar(sim, "#39FF14" if sim > 0.7 else "#FFE600" if sim > 0.5 else "#B26BFF")}
                <div class="chunk-footer">chunk #{cidx + 1} &middot; match {sim:.0%}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#B8ADD6; font-size:0.8rem; text-align:center; margin-top:24px;">Ask a question to see retrieved chunks here</p>', unsafe_allow_html=True)