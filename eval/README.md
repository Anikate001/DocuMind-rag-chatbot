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

_Run the harness and paste the printed table here._
