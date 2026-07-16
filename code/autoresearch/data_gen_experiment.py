"""QuitTxt Data-Generation Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_data_gen_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = (
    "Exp17 (prove-by-verbatim-quote gate, parent exp_0013): exp_0016 showed a plain "
    "self-audit is INERT (dropped 0 pairs; rag_q_11 invention survived; added NEW "
    "inventions rag_q_04/13 -> inflated faith, regressed quality dims). This replaces "
    "it with a HARD gate: emit a pair ONLY if a verbatim contiguous source span "
    "states its core claim; drop anything resting on world-knowledge/inference. {n}=10 "
    "is a CEILING, not a quota. Predict combined DROPS below exp_0013 0.66 as the "
    "leniency inflation (rag_q_04/11/13 invented pairs) honestly disappears into "
    "refusals, with quality dims (spec/ground/clin) UP from fewer invented pairs. "
    "count=10 ceiling/top_k=6/3-pass register UNCHANGED. Inherited note: "
    "Exp13 (retrieval-depth x breadth combo, parent exp_0009): QA_PER_SOURCE 8->10 "
    "(50 pairs) + RAG_TOP_K 3->6, both applied symmetrically. Tests whether deeper "
    "retrieval rescues the headline pair that 50-pair crowding displaced out of top-3 "
    "in facttype-lane (count=10 at top_k=3), while retaining that lane's behavioral "
    "conversion (rag_q_02). Register mechanism below inherited from exp_0009 "
    "UNCHANGED. Inherited note: "
    "Exp9 (tone lane, parent exp_0005): register-translation, FACT-FORWARD variant "
    "of exp_0006. exp_0006's 3-pass texting-register mechanism won tone 0.66->0.80 "
    "(+grd/+clin) but regressed faith 0.385->0.30 via retrieval displacement: warm "
    "empathetic openers ('You're not the only one—') diluted pair embeddings, "
    "flipping rag_q_01/10/16 to refusals under top_k=3. Fix: the translated ANSWER "
    "must LEAD with the concrete grounded fact (number/medication/term first); "
    "warmth and second-person address are a brief TRAILING clause, never a preamble "
    "before the fact. Keeps texting tone + protects retrievability and specificity."
)

# --- Generation model ---
# Options: "gpt-4o-mini", "gpt-4o"
GEN_MODEL = "gpt-4o-mini"

# --- Generation parameters ---
GEN_TEMPERATURE = 0.0       # maximum determinism — zero creative extrapolation
GEN_MAX_TOKENS = 3600       # room for the candidate pool + PASS-4 verbatim-quote gate
QA_PER_SOURCE = 10

# --- Generation prompt ---
# Must contain {n} placeholder for number of pairs to generate.
# The agent's source content is appended as a user message automatically.
GEN_SYSTEM_PROMPT = (
    "You are a smoking cessation counseling expert generating training data "
    "for a medical AI chatbot used in a healthcare setting.\n\n"
    "TASK: From the provided source content, produce AT MOST {n} question-answer "
    "pairs using a FOUR-PASS approach. {n} is a CEILING, never a quota: a pair is "
    "emitted ONLY if you can point to the exact words in the source that state it. "
    "Emitting 7 fully-sourced pairs is BETTER than 10 that include any unsourced "
    "claim.\n\n"
    "CRITICAL CONSTRAINT — HEALTHCARE SAFETY:\n"
    "This is a health domain. Do NOT add, infer, or invent FACTS beyond what the "
    "source explicitly states. Numbers, medication names, dosages, timeframes, and "
    "percentages are LOCKED — they must appear exactly as written in the source.\n\n"
    "PASS 1 — FACT EXTRACTION (build a candidate pool):\n"
    "First, read the source and mentally identify a pool of up to {n}+4 candidate "
    "facts, statistics, medication names, techniques, or clinical findings. For each "
    "candidate, note the exact phrase in the source that states it. Some candidates "
    "will be weaker than others — that is expected; PASS 4 will drop the ones you "
    "cannot fully source, so you are NOT committed to keeping all of them.\n\n"
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
    "- Answer: how a warm counselor would TEXT back — 2-3 short sentences that "
    "speak directly to the person ('you', 'your'). CRITICAL ORDERING: the answer "
    "must OPEN with the concrete grounded fact — the number, medication name, "
    "timeframe, percentage, or key clinical term appears in the FIRST sentence. Any "
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
    "PASS 4 — PROVE-BY-QUOTE GATE (this decides what is emitted):\n"
    "Register translation (PASS 3) may reword, but it must NOT have introduced "
    "anything the source does not literally contain. Audit each candidate ONE AT A "
    "TIME against this single test:\n"
    "  Can you copy a VERBATIM contiguous span of words FROM THE SOURCE that states "
    "the answer's core claim (its specific number, name, finding, or statement)?\n"
    "- If YES: keep the pair. The register wording can differ, but the fact it "
    "carries must be present word-for-word in that quoted span.\n"
    "- If NO — because the answer rests on general knowledge, common sense, medical "
    "training, or plausible inference rather than words ACTUALLY PRESENT in this "
    "source — the pair is UNVERIFIED. DROP it. Do not soften it into a partial "
    "answer; drop the whole pair.\n"
    "FORBIDDEN even when factually true in the real world: any claim you cannot quote "
    "from THIS source. Watch especially for these invention patterns and DROP them "
    "unless the source literally spells them out: answering a 'why does X happen' "
    "question with a plausible list of causes, reasons, or motivations the source "
    "never states; giving generic best-practice or 'how to' advice; asserting a "
    "well-known medical fact that this particular source simply does not mention.\n"
    "Emit only the pairs that pass this gate, up to the {n} ceiling. If fewer than "
    "{n} pass, emit only those — returning 6-8 fully-quoted pairs is the correct "
    "outcome; NEVER add an unquotable pair to reach {n}.\n\n"
    "RULES:\n"
    "1. Every fact in every answer must trace to a specific sentence in the source; "
    "only the wording is translated, never the clinical content.\n"
    "2. Warmth and direct address are TONE, not information — never introduce a "
    "fact, reassurance, or claim the source does not support.\n"
    "3. Cover {n} DIFFERENT topics — no repeated themes.\n"
    "4. No disclaimers, hedging, or generic advice unless the source says it.\n"
    "5. Emit only pairs that pass the PASS-4 prove-by-quote gate. Fewer fully-sourced "
    "pairs beats {n} padded with an unquotable one. Never invent to reach the count.\n\n"
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
RAG_TOP_K = 6
