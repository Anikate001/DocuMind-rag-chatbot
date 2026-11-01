# DocuMind evaluation

A repeatable test of DocuMind's retrieval and answers, used to pick the chunking strategy.

## What it measures

| Stage | Metric | Meaning |
|---|---|---|
| Retrieval (free) | **Recall@1 / @3 / @5** | % of answerable questions where the evidence is in the top 1 / 3 / 5 retrieved chunks |
| Retrieval (free) | **MRR** | How high the right chunk ranks (1.0 = always first) |
| Generation (Groq) | **Correctness** | LLM judge: answer matches the reference answer |
| Generation (Groq) | **Faithfulness** | LLM judge: every claim is supported by the retrieved context |
| Generation (Groq) | **Refusal accuracy** | % of unanswerable questions where DocuMind declined instead of guessing |

The harness reuses the app's own chunking, `all-MiniLM-L6-v2` embeddings, 0.3 similarity threshold,
top-5 retrieval and Groq prompt, but searches in memory, so it never writes to Supabase.

## Test document and golden set

`aquapilot_x3_manual.pdf` (11 pages, built by `make_test_pdf.py`) is a **fictional** product manual.
Because no LLM has seen its facts during training, a correct answer can only come from retrieval;
a famous public document would let the model answer from memory and inflate the scores. It also contains
deliberate distractors (a legacy X2 model with different specs, city tables, an FAQ) to test retrieval precision.

`golden_set.json` has 40 questions: 30 answerable (reference answer + evidence keywords) and 10 that the
manual cannot answer. `golden_set_attention.json` is an optional extra set for *Attention Is All You Need*.

## Run it

```bash
# Retrieval only (free, ~2 min)
python eval/run_eval.py --retrieval-only

# Full run (needs GROQ_API_KEY in .env)
python eval/run_eval.py
```

Or run everything in Google Colab with `eval/DocuMind_eval_colab.ipynb`.

LLM calls are cached in `eval/cache.json`. If Groq's free daily limit stops the run, run the same command
again later and it continues where it left off.

## Results

Retrieval stage on the AquaPilot X3 golden set (30 answerable questions, all-MiniLM-L6-v2, threshold 0.3, top-5), run in Google Colab:

| Chunk (words) | Overlap | Chunks | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---|---|---|---|---|
| **100** | 10 | 36 | **67%** | **87%** | **93%** | **0.77** |
| 200 | 20 | 18 | 57% | 70% | 70% | 0.62 |
| 300 | 30 | 12 | 53% | 60% | 70% | 0.58 |
| 500 (previous default) | 50 | 8 | 47% | 57% | 57% | 0.51 |

**Finding:** with 500-word chunks, recall@5 equals recall@3 because long chunks dilute the cosine
similarity below the 0.3 relevance threshold, so relevant chunks are filtered out before the top 5.
Switching to 100-word chunks raised recall@5 from 57% to 93% and MRR from 0.51 to 0.77, and the app now
uses 100-word chunks by default (`CHUNK_SIZE` / `CHUNK_OVERLAP` in `config.py`).

_Generation-stage results (correctness, faithfulness, refusal accuracy) will be added after the Groq run._
