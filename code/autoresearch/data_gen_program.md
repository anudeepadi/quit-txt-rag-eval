# Data-Generation Autoresearch Program

You are an autonomous research agent optimizing the **QA data generation prompt** for a smoking cessation RAG system. Your goal: produce AI-generated QA datasets that **match or surpass human-curated quality** when used as a RAG knowledge base.

## Context

- **Current state**: AI-generated KB achieves 91–102% of human-curated KB performance (p=0.184, not statistically significant). We want to close this gap — or push past it.
- **The problem**: The generation prompt determines the quality of every QA pair in the AI knowledge base. Better prompts → better QA pairs → better RAG answers → higher faithfulness.
- **Model for generation**: GPT-4o-mini (configurable)
- **Scoring**: Combined metric (0–1) weighted across:
  - RAG faithfulness (40%) — how well the generated KB supports RAG answers
  - Specificity (20%) — clinical detail in generated answers
  - Conversational tone (10%) — question naturalness
  - Groundedness (15%) — no hallucinations in generated answers
  - Clinical accuracy (15%) — medical correctness
- **Benchmark**: Human KB evaluated on same pipeline = the score to beat
- **Each experiment**: ~2–3 minutes, generates from 5 source chunks × 8 QA pairs = 40 pairs

## Your Files

| File | Role | Who Modifies |
|------|------|-------------|
| `data_gen_experiment.py` | Config variables + generation prompt | **YOU** (the agent) |
| `run_data_gen_experiment.py` | Evaluation harness | Do NOT modify |
| `data_gen_prepare.py` | Data loading + scoring utilities | Do NOT modify |
| `data_gen_program.md` | These instructions | The human |
| `data_gen_results.tsv` | Experiment log | Auto-generated |

## Setup (first time only)

```bash
cd gemini-protocol/code
python3 autoresearch/data_gen_prepare.py   # validate environment
```

## Experiment Loop

### 1. Read Context
- Read `data_gen_results.tsv` to see what's been tried and what worked
- Read `data_gen_experiment.py` to see the current generation prompt
- Study the human-curated QA pairs in `datasets/human-rag/human_curated_qa.jsonl` to understand what "gold standard" looks like
- Identify what dimension (specificity, tone, groundedness, clinical) is weakest

### 2. Form a Hypothesis
Before each change, write a clear hypothesis:
- "Adding 'include medication names and dosages when available' will boost specificity"
- "Requiring 'phrase questions as SMS texts under 15 words' will improve conversational tone"
- "Adding a chain-of-thought step ('First identify key facts, then compose the answer') will improve groundedness"
- "Requiring numbered source citations will reduce hallucination"

### 3. Modify data_gen_experiment.py
Change ONE variable at a time. The primary lever is `GEN_SYSTEM_PROMPT`.
Update `HYPOTHESIS` to describe what you're testing.

### 4. Run the Experiment
```bash
cd gemini-protocol/code
python3 autoresearch/run_data_gen_experiment.py
```

### 5. Evaluate
- **KEEP**: combined score improved → note what worked, move to next hypothesis
- **DISCARD**: revert `data_gen_experiment.py`, try a different approach
- Study which quality dimension improved/regressed and why
- Check the "relative to human" percentage — that's the ultimate metric

### 6. Repeat
Each experiment is ~2–3 minutes. Run as many as you can.

## What You Can Modify in data_gen_experiment.py

### GEN_SYSTEM_PROMPT (most impactful)
The system prompt used to generate QA pairs from source content. Must contain `{n}` placeholder.

**Strategies to explore (roughly in priority order):**

#### Specificity boosters
- "Include specific medication names (e.g., Varenicline/Chantix, Bupropion/Zyban), dosages, and treatment durations"
- "Include exact timeframes, percentages, and statistics from the source"
- "Each answer must contain at least 2 verifiable clinical facts"
- "Avoid vague phrases like 'talk to your doctor' or 'many people find' — replace with specifics"

#### Conversational tone
- "Questions should sound like a text message someone would send to a quit-smoking helpline"
- "Use first-person phrasing: 'I've been smoking for 10 years...' not 'What are the effects...'"
- "Include emotional context: anxiety, frustration, hope, skepticism"
- "Vary question length: mix short ('Is vaping safer?') with longer scenario-based questions"

#### Groundedness / anti-hallucination
- "Before writing each answer, mentally identify which sentences in the source support it"
- "If the source doesn't cover a topic, DO NOT generate a pair for it — generate fewer pairs if needed"
- "Add a self-check: could a reader verify every claim in your answer against the source text?"
- "Use direct quotes or close paraphrases from the source rather than rewriting from memory"

#### Structural experiments
- "Generate in two passes: first list the key facts, then compose QA pairs from that list"
- "For each pair, include a 'source_excerpt' field with the exact text supporting the answer"
- XML-wrapped context: `<source>...</source>` tags around the knowledge
- Numbered context chunks for explicit referencing

#### Answer format
- Vary answer length: "2-3 sentences" vs "4-6 sentences" vs "exactly 3 bullet points"
- "Write at an 8th-grade reading level"
- "End each answer with a concrete next step the person can take"
- "Structure answers as: acknowledge feeling → provide fact → suggest action"

### GEN_TEMPERATURE (0.0–1.0)
Lower = more deterministic/grounded. Higher = more diverse/creative questions.
- 0.0–0.2: maximum groundedness, may reduce question diversity
- 0.3–0.5: balanced (default is 0.3)
- 0.6–0.8: more creative questions, risk of hallucinated answers

### QA_PER_SOURCE (4–12)
More pairs per chunk = more coverage but risk of repetition.
Fewer pairs = higher quality per pair.

### GEN_MODEL
- "gpt-4o-mini": fast, cheap, good baseline
- "gpt-4o": slower, costlier, potentially higher quality

## Strategy Guidelines

1. **Start with the generation prompt** — it accounts for 80%+ of variance, just like in the RAG autoresearch
2. **Study the human KB** — read 20–30 human QA pairs, identify what makes them good. Then encode those qualities into the prompt
3. **One variable at a time** — clean attribution of what helped
4. **Watch the breakdown** — if specificity jumps but tone drops, address both
5. **Target the weakest dimension** — biggest bang for the buck
6. **Cross-reference with human baseline** — the relative % is what matters for the paper
7. **Diminishing returns** — if you plateau, try a radically different prompt architecture (e.g., two-pass generation, few-shot examples)
8. **Track what fails** — DISCARD results are informative

## Advanced Strategies (after initial exploration)

### Few-shot prompting
Add 2–3 exemplary human QA pairs directly in the prompt as examples of the quality bar.

### Two-pass generation
First pass: extract key facts from source. Second pass: compose QA pairs from facts.
(Implement by modifying the prompt to include both steps.)

### Adversarial self-critique
"After generating each pair, check: (1) is every claim in the source? (2) would a patient actually ask this? (3) is there a more specific answer? If any check fails, revise the pair."

### Category-aware generation
"Generate 2 pairs about medications, 2 about withdrawal symptoms, 2 about coping strategies, 2 about health benefits" — ensures topical diversity.

## When to Stop

- You've run 50+ experiments without improvement
- Combined score exceeds 0.92
- Relative to human exceeds 110% (AI > human)
- You're cycling through already-tested variations

## Safety

- Never modify `data_gen_prepare.py` or `run_data_gen_experiment.py`
- Never delete `data_gen_results.tsv` (it's your memory)
- Never hardcode answers or game the metric
- If the API errors, wait 60 seconds and retry
- Keep hypothesis descriptions informative — they're the only record of what you tried
