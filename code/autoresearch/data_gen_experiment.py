"""QuitTxt Data-Generation Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_data_gen_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = (
    "PASS-1 additive breadth (epoch 2, parent exp_0005 combined 0.6363): keep "
    "headline/clinical fact extraction FIRST, then ALSO capture practical/"
    "behavioral facts the source explicitly states (coping/self-management "
    "strategies, how-to guidance, prevention approaches, motivations/drivers, "
    "who-is-affected, everyday-life effects). Raise QA_PER_SOURCE 8->10 to fund "
    "the added breadth without displacing definitional pairs. Goal: convert "
    "domain-present refusal-zeros into answered questions under deterministic "
    "epoch-2 refusal scoring while holding groundedness >=0.90 and keeping the "
    "definitional-coverage canary passing."
)

# --- Generation model ---
# Options: "gpt-4o-mini", "gpt-4o"
GEN_MODEL = "gpt-4o-mini"

# --- Generation parameters ---
GEN_TEMPERATURE = 0.0       # maximum determinism — zero creative extrapolation
GEN_MAX_TOKENS = 2500
QA_PER_SOURCE = 10

# --- Generation prompt ---
# Must contain {n} placeholder for number of pairs to generate.
# The agent's source content is appended as a user message automatically.
GEN_SYSTEM_PROMPT = (
    "You are a smoking cessation counseling expert generating training data "
    "for a medical AI chatbot used in a healthcare setting.\n\n"
    "TASK: From the provided source content, generate exactly {n} question-answer "
    "pairs using a TWO-PASS approach.\n\n"
    "CRITICAL CONSTRAINT — HEALTHCARE SAFETY:\n"
    "This is a health domain. Do NOT add, infer, or rephrase beyond what the "
    "source explicitly states.\n\n"
    "PASS 1 — FACT EXTRACTION:\n"
    "First, read the source and mentally identify the {n} most important distinct "
    "facts. The source contains TWO kinds of content — capture both:\n"
    "  (a) Headline/clinical facts: definitions, statistics, medication names, "
    "techniques, mechanisms, and clinical findings. Always capture these first — "
    "they are the backbone of the knowledge base.\n"
    "  (b) Practical/behavioral facts: coping and self-management strategies, "
    "how-to guidance, prevention approaches, motivations or drivers of behavior, "
    "who is affected, and everyday-life effects — WHENEVER the source explicitly "
    "states them. These are easy to overlook next to clinical findings but are "
    "equally valid, directly-stated facts.\n"
    "Each extracted fact must be directly stated in the source text; do NOT "
    "invent practical advice the source does not contain.\n\n"
    "PASS 2 — QA PAIR COMPOSITION:\n"
    "For each extracted fact, compose one question-answer pair:\n"
    "- Question: conversational, first-person, like texting a quit-smoking chatbot\n"
    "- Answer: 2-3 sentences using the source's own words. Include specific details "
    "(medication names, dosages, timeframes, percentages) exactly as written in "
    "the source. Do NOT paraphrase clinical terms or numbers.\n\n"
    "RULES:\n"
    "1. Every claim in every answer must trace to a specific sentence in the source.\n"
    "2. Cover {n} DIFFERENT topics — no repeated themes.\n"
    "3. No disclaimers, hedging, or generic advice unless the source says it.\n"
    "4. If the source doesn't contain {n} distinct facts, generate fewer pairs.\n\n"
    "Return a JSON object with key \"qa_pairs\" containing an array of objects, "
    "each with \"question\" (string) and \"answer\" (string) fields only."
)

# --- RAG evaluation config (how the generated data is tested) ---
# These stay constant so we only measure the effect of the generation prompt.
RAG_TEMPLATE = (
    "You are a smoking cessation counselor.\n"
    "Answer the question in 2-3 sentences using ONLY facts from the "
    "knowledge base below.\n"
    "Do NOT add information, examples, or details not explicitly stated "
    "in the knowledge base.\n\n"
    "KNOWLEDGE BASE:\n{knowledge}"
)
RAG_TEMPERATURE = 0.3
RAG_MAX_TOKENS = 150
RAG_TOP_K = 3
