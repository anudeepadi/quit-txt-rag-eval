# autoresearch/ — Autonomous RAG Optimization

An iterative experiment loop where an AI agent autonomously tunes RAG parameters to maximize faithfulness.

## Architecture

```
program.md          ← Agent reads this for instructions
    ↓
experiment.py       ← Agent MODIFIES this (hypothesis, config, params)
    ↓
run_experiment.py   ← Agent RUNS this (loads config → eval → score → log)
    ↓
results.tsv         ← Append-only experiment log
    ↑
prepare.py          ← Fixed infrastructure (NEVER modified by agent)
```

## Files

| File | Role | Modified by agent? |
|---|---|---|
| `program.md` | Instructions for the autonomous agent | No |
| `experiment.py` | Configuration: hypothesis, target_config, temperature, max_tokens, top_k, RAG template | **Yes** |
| `run_experiment.py` | Experiment harness: loads config, runs eval on 20 questions, scores, logs | No |
| `prepare.py` | Infrastructure: dataset loading, ChromaDB building, LLM-as-judge scoring, result logging | No |
| `results.tsv` | Experiment log with columns: experiment_id, timestamp, hypothesis, target_config, faithfulness_proxy, word stats, params, verdict | Append-only |

## How It Works

1. Agent reads `program.md` for optimization strategy
2. Agent modifies `experiment.py` with a new hypothesis and parameters
3. Agent runs `python3 autoresearch/run_experiment.py`
4. Harness evaluates 20 test questions with the specified config
5. Each response is scored by LLM-as-judge (GPT-4o-mini rates grounding 0–10)
6. Average faithfulness proxy is logged to `results.tsv` with KEEP/DISCARD verdict
7. Agent analyzes results and iterates

## Scoring

The **faithfulness proxy** uses LLM-as-judge:
- GPT-4o-mini rates how well each response is grounded in its retrieved contexts
- Scale: 0 (entirely fabricated) to 10 (every claim supported)
- Normalized to 0.0–1.0
- Fast alternative to full RAGAS faithfulness (which requires async batching and rate limit management)

## Current Results

Best score: **0.885** (human_rag, concise prompting, temp=0.3, max_tokens=150, top_k=3)
