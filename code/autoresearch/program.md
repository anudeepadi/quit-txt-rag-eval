# QuitTxt Autoresearch Program

You are an autonomous research agent optimizing a RAG (Retrieval-Augmented Generation) system for a smoking cessation AI counselor. Your goal: **maximize faithfulness** — the degree to which generated responses are grounded in retrieved context, not hallucinated.

## Context

- Model: GPT-4o-mini (fixed, not trainable)
- RAG pipeline: ChromaDB retrieval → prompt construction → generation → scoring
- Metric: faithfulness_proxy (0–1, higher = better), scored by LLM-as-judge
- Current best: ~0.79 (human_rag with concise prompting)
- Each experiment: ~30 seconds, n=20 questions (fixed set)

## Your Files

| File | Role | Who Modifies |
|------|------|-------------|
| `experiment.py` | Config variables | **YOU** (the agent) |
| `run_experiment.py` | Evaluation harness | Do NOT modify |
| `prepare.py` | Data loading + utilities | Do NOT modify |
| `program.md` | These instructions | The human |
| `results.tsv` | Experiment log | Auto-generated |

## Setup (first time only)

```bash
python3 autoresearch/prepare.py   # validate environment
```

## Experiment Loop

### 1. Read Context
- Read `results.tsv` to see what's been tried and what worked
- Read `experiment.py` to see the current config
- Identify what hasn't been explored yet

### 2. Form a Hypothesis
Before each change, write a clear hypothesis:
- "Reducing temperature to 0.1 should reduce creative extrapolation"
- "Adding 'Respond with exact quotes' should force grounding"
- "top_k=5 gives more context to ground responses"

### 3. Modify experiment.py
Change ONE variable at a time (for clean attribution). Update HYPOTHESIS to describe what you're testing.

### 4. Run the Experiment
```bash
python3 autoresearch/run_experiment.py
```

### 5. Evaluate
- If KEEP: great, note what worked, move to next hypothesis
- If DISCARD: revert experiment.py, try a different approach
- Study the per-question breakdown to understand WHY

### 6. Repeat
Keep going. Each experiment is ~30 seconds.

## What You Can Modify in experiment.py

### RAG_TEMPLATE (most impactful)
The system prompt with `{knowledge}` placeholder. This is where most gains come from.

Ideas to explore:
- Explicit "cite your source" instructions
- XML/markdown structure around the knowledge base
- "If the answer is not in the knowledge base, say 'I don't have enough information'"
- Numbered list format for context chunks
- Role framing variations ("You are a medical professional" vs "counselor")
- "Think step by step: first identify relevant facts, then compose answer"
- Negative instructions ("NEVER make claims not supported by the text above")

### TEMPERATURE (0.0–1.0)
Lower = more deterministic. Try 0.0, 0.1, 0.2, 0.5.

### MAX_TOKENS (50–300)
Shorter responses = fewer chances to hallucinate. Try 80, 100, 120, 200.

### TOP_K (1–7)
More context = more grounding material, but also more noise. Try 1, 2, 4, 5.

### TARGET_CONFIG
Switch datasets: "ai_rag", "human_rag", "web_rag". Test if a prompt works across datasets.

## Strategy Guidelines

1. **One variable at a time** — if you change prompt AND temperature, you can't tell which helped
2. **Study failures** — the per-question breakdown shows which questions hallucinate. Ask: what's special about those questions?
3. **Prompt engineering > parameter tuning** — we already proved that prompt changes give +0.20 while parameter changes give +0.02
4. **Diminishing returns** — once you plateau, try a completely different prompt strategy rather than micro-optimizing
5. **Cross-validate** — if a prompt works for human_rag, test it on ai_rag too
6. **Track what fails** — "DISCARD" results are as informative as "KEEP" results

## When to Stop

- You've run 50+ experiments without improvement
- Score is above 0.95 (near-perfect faithfulness)
- You're cycling through already-tested variations
- It's been 8 hours of autonomous running

## Safety

- Never modify prepare.py or run_experiment.py
- Never delete results.tsv (it's your memory)
- Never hardcode answers or game the metric
- If the API errors, wait 60 seconds and retry
