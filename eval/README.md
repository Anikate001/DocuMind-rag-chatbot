# DocuMind evaluation

A repeatable test of DocuMind's retrieval and answers, used to pick the chunking strategy.

## What it measures

| Stage | Metric | Meaning |
|---|---|---|
| Retrieval (free) | **Recall@5** | % of answerable questions where one of the top-5 retrieved chunks contains the evidence |
| Retrieval (free) | **MRR** | How high the right chunk ranks (1.0 = always first) |
| Generation (Groq) | **Correctness** | LLM judge: answer matches the reference answer |
| Generation (Groq) | **Faithfulness** | LLM judge: every claim is supported by the retrieved context |
| Generation (Groq) | **Refusal accuracy** | % of unanswerable questions where DocuMind declined instead of guessing |

The harness reuses the app's own chunking, `all-MiniLM-L6-v2` embeddings, 0.3 similarity threshold,
top-5 retrieval and Groq prompt, but searches in memory, so it never writes to Supabase.

## Golden set

`golden_set.json` has 40 questions about *Attention Is All You Need* (Vaswani et al., 2017):
30 answerable (with a reference answer and evidence keywords) and 10 the paper cannot answer.

## Run it

```bash
# 1. Download the paper (latest arXiv version) into eval/
curl -L -o eval/attention_is_all_you_need.pdf https://arxiv.org/pdf/1706.03762

# 2. Retrieval only (free, ~2 min)
python eval/run_eval.py --pdf eval/attention_is_all_you_need.pdf --retrieval-only

# 3. Full run (needs GROQ_API_KEY in .env)
python eval/run_eval.py --pdf eval/attention_is_all_you_need.pdf
```

On Windows PowerShell, download step 1 in a browser instead and save the file into the `eval` folder.

LLM calls are cached in `eval/cache.json`. If Groq's free daily limit stops the run, run the same command
again later and it continues where it left off.

## Results

_Run the harness and paste the printed table here._
