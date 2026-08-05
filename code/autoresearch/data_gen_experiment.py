"""QuitTxt Data-Generation Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_data_gen_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = (
    "Rationale-as-fact coverage: PASS-1 extracts source-STATED reasons/motivations/"
    "affected-groups as first-class facts, PASS-3 gains the consumer motivation "
    "question framing, Rule 3 permits a stated reason alongside the fact it explains. "
    "Expected: +0.02 to +0.05 combined vs exp_0025 (0.8286/0.8214), driven by "
    "motivation/demographic-framed refusal zeros converting on the dev split"
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
    "pairs using a THREE-PASS approach.\n\n"
    "CRITICAL CONSTRAINT — HEALTHCARE SAFETY:\n"
    "This is a health domain. Do NOT add, infer, or invent FACTS beyond what the "
    "source explicitly states. Numbers, medication names, dosages, timeframes, and "
    "percentages are LOCKED — they must appear exactly as written in the source.\n\n"
    "PASS 1 — FACT EXTRACTION:\n"
    "First, read the source and mentally identify the {n} most important distinct "
    "facts, statistics, medication names, techniques, or clinical findings. Each "
    "fact must be directly stated in the source text.\n"
    "A STATED REASON COUNTS AS A FACT. When the source explicitly says WHY something "
    "works, why people choose it, what it protects against, or WHICH GROUP it affects "
    "— a 'because', 'so that', 'this helps', 'to avoid', 'allows', 'the impact is "
    "stronger among' clause — that stated reason or group is an extractable fact in "
    "its own right, not decoration on the instruction it accompanies. Shape to look "
    "for: '<do this> so that <this happens>' yields two facts, the instruction and "
    "the stated payoff; '<effect> is stronger among <group>' yields the effect and "
    "the group. Extract only reasons the source states outright; never supply a "
    "reason the source omits.\n\n"
    "PASS 2 — GROUNDED DRAFT (internal scaffolding, NOT in the output):\n"
    "For each extracted fact, mentally write one plain clinical sentence that "
    "captures the fact with every number, dose, timeframe, and percentage from the "
    "source verbatim. This locks the content before you touch the wording.\n\n"
    "PASS 3 — REGISTER TRANSLATION (this produces the output pair):\n"
    "Translate each grounded draft into a real text-message exchange between a "
    "person trying to quit and their chatbot counselor. The clinical content is "
    "fixed; ONLY the register changes.\n"
    "- Question: what the REAL PERSON would actually text about their own body, "
    "life, or worry — first or second person ('my', 'I', 'me', 'you'). NEVER an "
    "academic, study, or textbook question. Do NOT open with 'How did researchers', "
    "'What methodology', or a bare 'What is <term>' definition request; a person "
    "texting a quit app never talks that way.\n"
    "  When the extracted fact is a STATED REASON or an AFFECTED GROUP, ask it the "
    "way a person asks about motives, not the way they ask for instructions: 'why "
    "would someone want to...', 'why does that even help', 'is there a reason people "
    "do X instead of Y', 'does this hit some people harder than others'. These "
    "motivation and who-it-affects framings are what a real person texts when they "
    "are deciding whether to bother — cover them, not only the how-to phrasing.\n"
    "- Answer: how a warm counselor would TEXT back — 2-3 short sentences that "
    "speak directly to the person ('you', 'your'). CRITICAL ORDERING: the answer "
    "must OPEN with the concrete grounded fact — the number, medication name, "
    "timeframe, percentage, or key clinical term appears in the FIRST sentence. When "
    "the fact is a stated reason or affected group, that reason or group is itself "
    "the concrete content and must lead the first sentence, in the source's own "
    "terms. Any "
    "warmth, reassurance, or empathy is a brief TRAILING clause AFTER the fact, "
    "never a preamble before it. Preserve every number, medication name, dosage, "
    "timeframe, and percentage from the grounded draft EXACTLY. Change the framing, "
    "never the facts.\n\n"
    "REGISTER EXAMPLE (fact leads; numbers survive; warmth trails):\n"
    "  Source: 'the proportion of individuals motivated to quit due to the cost of "
    "smoking increased from 38% in 2007 to 57% in 2019, making it the most common "
    "reason since 2013.'\n"
    "  Weak (academic third-person, tone~0.3): Q 'Has the rising cost of cigarettes "
    "influenced people to quit smoking?' / A 'Studies indicate the proportion of "
    "individuals motivated to quit due to cost increased from 38% in 2007 to 57% in "
    "2019.'\n"
    "  Bad (warm but fact buried, hurts retrieval): A \"You're not the only one "
    "feeling this — and cost went from 38% up to 57%.\"\n"
    "  Strong (fact-forward texting, tone~0.9): Q 'Is the price finally what pushes "
    "people to quit, or is that just me?' / A \"The share of people quitting because "
    "of cost jumped from 38% in 2007 to 57% by 2019, and it's been the top reason "
    "since 2013 — so you're definitely not the only one feeling that.\"\n\n"
    "RULES:\n"
    "1. Every fact in every answer must trace to a specific sentence in the source; "
    "only the wording is translated, never the clinical content.\n"
    "2. Warmth and direct address are TONE, not information — never introduce a "
    "fact, reassurance, or claim the source does not support.\n"
    "3. Cover {n} DIFFERENT topics — no repeated themes. One exception: a stated "
    "reason may be paired with the practical fact it explains, because 'what do I "
    "do' and 'why does that work' are two different questions a person asks. The two "
    "answers must not restate each other.\n"
    "4. No disclaimers, hedging, or generic advice unless the source says it.\n"
    "5. If the source doesn't contain {n} distinct facts, generate fewer pairs.\n\n"
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
