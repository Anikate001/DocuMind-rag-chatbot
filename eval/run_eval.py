"""
DocuMind evaluation harness
===========================

Answers the question: "How good is DocuMind, and which chunking strategy is best?"

It reuses the app's real pieces:
  * text extraction + word chunking  (text_utils.py)
  * all-MiniLM-L6-v2 embeddings, cosine similarity, 0.3 threshold, top-5  (same as match_chunks)
  * the exact Groq answer prompt  (llm.answer_with_citations)

Retrieval is done in memory, so the eval never touches your Supabase tables.

Metrics
-------
Stage 1 - retrieval (free, no API calls, runs for every chunking config):
  recall@k     share of answerable questions where a retrieved chunk contains the evidence
  MRR          mean reciprocal rank of the first chunk with the evidence (1.0 = always ranked first)

Stage 2 - generation (uses Groq, runs for the configs you choose, default = app default + best):
  correctness   LLM judge: does the answer match the reference answer?
  faithfulness  LLM judge: is every claim supported by the retrieved context?
  refusal acc.  share of unanswerable questions where DocuMind declined instead of making something up

Usage (from the repo root, with GROQ_API_KEY in .env):
  python eval/run_eval.py                    # default test PDF + golden set
  python eval/run_eval.py --retrieval-only   # free, no Groq calls

Groq's free tier has daily token limits. Every LLM call is cached in eval/cache.json,
so if you hit a 429 limit just run the same command again later and it resumes.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from text_utils import extract_text_from_pdf, chunk_text, format_context  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
CACHE_FILE = EVAL_DIR / "cache.json"

CONFIGS = [  # (chunk_size_words, overlap_words)
    (100, 10),
    (200, 20),
    (300, 30),
    (500, 50),   # current app default
]
APP_DEFAULT = (500, 50)
TOP_K = 5
THRESHOLD = 0.3                       # same as retriever.py
JUDGE_MODEL = "llama-3.1-8b-instant"  # cheaper on the free tier; generation still uses the app's 70B model
REFUSAL_TEXT = "I couldn't find relevant information in the uploaded documents."


# ----------------------------------------------------------------------------- retrieval
def load_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def build_index(embedder, text, size, overlap, filename):
    chunks = chunk_text(text, chunk_size=size, overlap=overlap)
    vecs = embedder.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
    rows = [{"content": c, "filename": filename, "chunk_index": i} for i, c in enumerate(chunks)]
    return rows, np.asarray(vecs)


def retrieve(embedder, rows, vecs, question, k=TOP_K, threshold=THRESHOLD):
    """Mirror of the match_chunks SQL function: cosine similarity, threshold, top-k."""
    q = embedder.encode([question], normalize_embeddings=True, show_progress_bar=False)[0]
    sims = vecs @ q
    order = np.argsort(-sims)
    out = []
    for idx in order[:k]:
        if sims[idx] < threshold:
            break
        out.append({**rows[idx], "similarity": float(sims[idx])})
    return out


def contains_evidence(chunk_text_, evidence):
    """A chunk 'contains the evidence' if it has every keyword in at least one evidence group."""
    t = " ".join(chunk_text_.lower().split())
    return any(all(kw.lower() in t for kw in group) for group in evidence)


def retrieval_metrics(embedder, rows, vecs, golden):
    ranks = []
    for item in golden:
        if not item["answerable"]:
            continue
        got = retrieve(embedder, rows, vecs, item["question"])
        ranks.append(next((i + 1 for i, c in enumerate(got) if contains_evidence(c["content"], item["evidence"])), None))
    n = len(ranks)
    rec = lambda k: round(sum(1 for r in ranks if r and r <= k) / n, 3)
    return {"recall@1": rec(1), "recall@3": rec(3), f"recall@{TOP_K}": rec(TOP_K),
            "mrr": round(sum(1.0 / r for r in ranks if r) / n, 3)}


# ----------------------------------------------------------------------------- LLM calls (cached)
_cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}


def cached(key_parts, fn):
    key = hashlib.sha256(json.dumps(key_parts, sort_keys=True).encode()).hexdigest()
    if key not in _cache:
        _cache[key] = fn()
        CACHE_FILE.write_text(json.dumps(_cache))
    return _cache[key]


def call_with_retry(fn, tries=6):
    for attempt in range(tries):
        try:
            return fn()
        except Exception as e:  # rate limit or transient error
            msg = str(e)
            if "401" in msg or "Invalid API Key" in msg:
                sys.exit("\nGroq rejected the API key (401). Check GROQ_API_KEY - Groq keys start with 'gsk_'.\n")
            if "tokens per day" in msg or "TPD" in msg:
                sys.exit("\nGroq daily token limit reached. Progress is cached; run the same command again tomorrow.\n")
            wait = 10 * (attempt + 1)
            print(f"   ...retrying in {wait}s ({msg[:80]})")
            time.sleep(wait)
    raise RuntimeError("Groq call kept failing")


def generate(question, chunks):
    """Exactly what app.py does for a chat message."""
    if not chunks:
        return REFUSAL_TEXT
    from llm import answer_with_citations
    context, citations = format_context(chunks)
    return call_with_retry(lambda: answer_with_citations(question, context, citations))


def judge(prompt):
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    def _call():
        r = client.chat.completions.create(
            model=JUDGE_MODEL, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(r.choices[0].message.content)
    return call_with_retry(_call)


def judge_correct(question, reference, answer):
    return bool(judge(f"""Grade a document-QA answer against a reference answer.
Mark correct=true if the ANSWER states the same key facts as the REFERENCE (wording may differ,
extra correct detail is fine). Mark false if it is wrong, missing the key fact, or says it could not find it.
Reply as JSON: {{"correct": true or false}}

QUESTION: {question}
REFERENCE: {reference}
ANSWER: {answer}""").get("correct", False))


def judge_faithful(context, answer):
    return bool(judge(f"""Is EVERY factual claim in the ANSWER supported by the CONTEXT?
Ignore citation markers like [1] and the "Sources used" list. If the answer only says it could not
find the information, mark supported=true.
Reply as JSON: {{"supported": true or false}}

CONTEXT:
{context}

ANSWER: {answer}""").get("supported", False))


def judge_refused(answer):
    return bool(judge(f"""Does this answer decline to answer / say the information is not in the documents,
rather than giving a substantive answer? Reply as JSON: {{"refused": true or false}}

ANSWER: {answer}""").get("refused", False))


def generation_metrics(embedder, rows, vecs, golden, tag):
    correct = faithful = answerable = refused = unanswerable = 0
    for i, item in enumerate(golden, 1):
        q = item["question"]
        chunks = retrieve(embedder, rows, vecs, q)
        ans = cached(["gen", tag, q], lambda: generate(q, chunks))
        if item["answerable"]:
            answerable += 1
            ctx, _ = format_context(chunks) if chunks else ("", [])
            correct += cached(["correct", tag, q], lambda: judge_correct(q, item["answer"], ans))
            faithful += cached(["faithful", tag, q], lambda: judge_faithful(ctx, ans))
        else:
            unanswerable += 1
            refused += cached(["refused", tag, q], lambda: judge_refused(ans))
        print(f"   [{i}/{len(golden)}] done", end="\r")
    print()
    return {
        "correctness": round(correct / max(answerable, 1), 3),
        "faithfulness": round(faithful / max(answerable, 1), 3),
        "refusal_accuracy": round(refused / max(unanswerable, 1), 3),
    }


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=str(EVAL_DIR / "aquapilot_x3_manual.pdf"))
    ap.add_argument("--golden", default=str(EVAL_DIR / "golden_set.json"))
    ap.add_argument("--retrieval-only", action="store_true", help="skip Groq calls (free)")
    ap.add_argument("--gen-configs", default="default,best",
                    help="which configs get the Groq stage: 'default,best' or 'all'")
    args = ap.parse_args()

    if not args.retrieval_only:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        if not os.getenv("GROQ_API_KEY"):
            sys.exit("GROQ_API_KEY not set (put it in .env) - or run with --retrieval-only")

    golden = json.loads(Path(args.golden).read_text())
    text = extract_text_from_pdf(Path(args.pdf).read_bytes())
    print(f"PDF: {Path(args.pdf).name} - {len(text.split()):,} words; "
          f"golden set: {sum(g['answerable'] for g in golden)} answerable + "
          f"{sum(not g['answerable'] for g in golden)} unanswerable questions\n")

    embedder = load_embedder()
    results, indexes = [], {}
    print("Stage 1 - retrieval")
    for size, overlap in CONFIGS:
        rows, vecs = build_index(embedder, text, size, overlap, Path(args.pdf).name)
        indexes[(size, overlap)] = (rows, vecs)
        m = retrieval_metrics(embedder, rows, vecs, golden)
        m.update(chunk_size=size, overlap=overlap, n_chunks=len(rows))
        results.append(m)
        print(f"  chunk={size:<4} overlap={overlap:<3} chunks={len(rows):<4} recall@1={m['recall@1']:.2f}  "
              f"recall@3={m['recall@3']:.2f}  recall@{TOP_K}={m[f'recall@{TOP_K}']:.2f}  MRR={m['mrr']:.2f}")

    best = max(results, key=lambda r: (r[f"recall@{TOP_K}"], r["mrr"], r["recall@1"]))
    print(f"\nBest retrieval config: chunk={best['chunk_size']}, overlap={best['overlap']}")

    if not args.retrieval_only:
        wanted = {(r["chunk_size"], r["overlap"]) for r in results} if args.gen_configs == "all" \
            else {APP_DEFAULT, (best["chunk_size"], best["overlap"])}
        print("\nStage 2 - generation (Groq)")
        for r in results:
            cfg = (r["chunk_size"], r["overlap"])
            if cfg not in wanted:
                continue
            print(f"  chunk={cfg[0]} overlap={cfg[1]}")
            rows, vecs = indexes[cfg]
            r.update(generation_metrics(embedder, rows, vecs, golden, tag=f"{cfg[0]}-{cfg[1]}"))

    out = EVAL_DIR / "results.json"
    out.write_text(json.dumps(results, indent=2))

    print("\n| Chunk (words) | Overlap | Chunks | Recall@1 | Recall@3 | Recall@5 | MRR | Correct | Faithful | Refusal |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        f = lambda k: f"{r[k]:.0%}" if k in r else "-"
        print(f"| {r['chunk_size']} | {r['overlap']} | {r['n_chunks']} | {r['recall@1']:.0%} | {r['recall@3']:.0%} | "
              f"{r[f'recall@{TOP_K}']:.0%} | {r['mrr']:.2f} | {f('correctness')} | {f('faithfulness')} | "
              f"{f('refusal_accuracy')} |")
    print(f"\nSaved {out.relative_to(ROOT)} - paste the table into README.md and send it to Claude.")


if __name__ == "__main__":
    main()
