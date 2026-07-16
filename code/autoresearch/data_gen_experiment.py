"""QuitTxt Data-Generation Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_data_gen_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = (
    "Dual-channel tone+specificity on the Exp5 two-pass base. TONE: rewrite the "
    "PASS-2 question instruction to force first-person real-person texting register "
    "and forbid researcher-framed phrasings (validated in exp_0001: tone 0.68->0.73). "
    "SPECIFICITY: add a SOFT PASS-1 bias to prefer source facts already carrying a "
    "concrete anchor (number/%/dose/timeframe/med/technique) when the source offers a "
    "choice, all-else-equal, without inventing anchors or dropping anchor-free topics "
    "(distinct from the discarded Exp11 hard-anchor gate). Answer composition rules "
    "unchanged to protect groundedness/faithfulness. temp=0.0, gpt-4o-mini."
)

# --- Generation model ---
# Options: "gpt-4o-mini", "gpt-4o"
GEN_MODEL = "gpt-4o-mini"

# --- Generation parameters ---
GEN_TEMPERATURE = 0.0       # maximum determinism — zero creative extrapolation
GEN_MAX_TOKENS = 2500
QA_PER_SOURCE = 8

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
    "facts, statistics, medication names, techniques, or clinical findings. Each "
    "fact must be directly stated in the source text. When the source offers a "
    "choice and all else is equal, prefer the more concrete version of a fact — the "
    "one that carries a specific number, percentage, dosage, timeframe, medication "
    "name, or named technique — over a vague or general phrasing of the same point. "
    "Do NOT invent an anchor the source lacks, and do NOT skip an important topic just "
    "because it has no number (topic coverage still comes first).\n\n"
    "PASS 2 — QA PAIR COMPOSITION:\n"
    "For each extracted fact, compose one question-answer pair:\n"
    "- Question: write it the way the SMOKER would actually text it — first person "
    "(\"I\", \"my\"), casual, lowercase-ok, often naming their real worry or situation. "
    "The person texting is someone trying to quit, NOT a researcher or clinician. Even "
    "when the source is written in academic or study-report language, do NOT echo that "
    "framing — never ask from a researcher's point of view (no \"how did researchers...\", "
    "\"what methodology...\", \"what is the efficacy of...\"). Translate the underlying fact "
    "into what a real person would thumb-type into a quit-line. Reframe examples:\n"
    "    \"What methodology did researchers use to measure nicotine's neural effects?\" -> "
    "\"does smoking actually mess with my brain right after a cigarette?\"\n"
    "    \"What are the pharmacological options for nicotine dependence?\" -> "
    "\"what meds actually help with quitting?\"\n"
    "    \"How does cessation affect cardiovascular recovery over time?\" -> "
    "\"if i quit now how long till my heart's back to normal?\"\n"
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
