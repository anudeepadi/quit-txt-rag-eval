"""QuitTxt Data-Generation Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_data_gen_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = (
    "Count-isolated additive extraction (epoch 3, parent exp_0019). SAME PASS-1 "
    "enumerated/secondary-fact instruction + softened Rule 2 as exp_0021, but KEEP "
    "QA_PER_SOURCE=8. Disentangles the extraction-instruction effect from exp_0021's "
    "count=10 pool-size shift, which redrew the seeded 15-pair quality sample and "
    "drove an unreliable spec +0.10 / tone -0.067 swing plus a tone-floor breach "
    "(0.64<0.68). Tests whether the instruction ALONE converts rag_q_09 (Easyway, "
    "id00625) at fixed n_pairs (facttype lane says extraction is zero-sum at count=8), "
    "and whether tone returns toward parent 0.707 with a parent-comparable sample."
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
    "fact must be directly stated in the source text.\n"
    "ALSO capture enumerated and secondary facts, not just headline ones:\n"
    "- When a source sentence lists multiple conditions, effects, affected groups, "
    "or items (e.g. a list of health conditions, several benefits, a set of "
    "symptoms), treat EACH listed item as its own extractable fact worth a distinct "
    "pair — do not collapse the list into one summary fact.\n"
    "- A fact stated as a secondary or side mention inside an answer about a broader "
    "topic is itself extractable, even when the broader topic is already covered by "
    "another pair.\n"
    "Every such fact must still be directly stated in the source text — never invent "
    "or infer an item that is not literally present.\n\n"
    "PASS 2 — QA PAIR COMPOSITION:\n"
    "For each extracted fact, compose one question-answer pair:\n"
    "- Question: conversational, first-person, like texting a quit-smoking chatbot\n"
    "- Answer: 2-3 sentences using the source's own words. Include specific details "
    "(medication names, dosages, timeframes, percentages) exactly as written in "
    "the source. Do NOT paraphrase clinical terms or numbers.\n\n"
    "RULES:\n"
    "1. Every claim in every answer must trace to a specific sentence in the source.\n"
    "2. Cover {n} DIFFERENT facts — no two pairs may state the same fact. Distinct "
    "facts that fall under the same broad subject (e.g. two different conditions from "
    "one health-effects list) are allowed and encouraged; only restating the same "
    "fact is disallowed.\n"
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
