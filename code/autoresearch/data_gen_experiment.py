"""QuitTxt Data-Generation Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_data_gen_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = (
    "Exp16 (roundtrip source-verification filter, parent exp_0013): add an "
    "overgenerate-then-self-verify PASS 4. PASS 1 drafts a pool of {n}+4 candidates; "
    "PASS 4 audits every claim in each candidate answer against an explicit source "
    "sentence and DISCARDS any pair whose content the source does not state, emitting "
    "only up to {n} verified pairs (fewer if fewer survive — never padded). Removes "
    "the count=10 self-referential-invention vector (project gaming-risk #1): the "
    "teen-initiation pair (peer-pressure/curiosity, source-absent) that self-scored "
    "faithful at rag_q_11 should now be dropped -> honest refusal (faith may drop "
    "~0.02, expected). Genuine conversions (rag_q_07/16 £38/wk savings) are "
    "source-grounded and must survive. GEN_MAX_TOKENS 2500->3600 for the extra "
    "drafts+audit. count=10/top_k=6 and the exp_0009 3-pass fact-forward register are "
    "UNCHANGED. Inherited note: "
    "Exp13 (retrieval-depth x breadth combo, parent exp_0009): QA_PER_SOURCE 8->10 "
    "(50 pairs) + RAG_TOP_K 3->6, both applied symmetrically. Register mechanism "
    "below inherited from exp_0009 UNCHANGED. Inherited note: "
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
GEN_MAX_TOKENS = 3600       # room for the +4 overgenerated drafts + PASS-4 verification
QA_PER_SOURCE = 10

# --- Generation prompt ---
# Must contain {n} placeholder for number of pairs to generate.
# The agent's source content is appended as a user message automatically.
GEN_SYSTEM_PROMPT = (
    "You are a smoking cessation counseling expert generating training data "
    "for a medical AI chatbot used in a healthcare setting.\n\n"
    "TASK: From the provided source content, produce {n} verified question-answer "
    "pairs using a FOUR-PASS approach. You OVERGENERATE candidates, then keep only "
    "the ones whose every claim is proven against the source.\n\n"
    "CRITICAL CONSTRAINT — HEALTHCARE SAFETY:\n"
    "This is a health domain. Do NOT add, infer, or invent FACTS beyond what the "
    "source explicitly states. Numbers, medication names, dosages, timeframes, and "
    "percentages are LOCKED — they must appear exactly as written in the source.\n\n"
    "PASS 1 — FACT EXTRACTION (OVERGENERATE):\n"
    "First, read the source and mentally identify a POOL of candidate facts — aim "
    "for {n}+4 distinct facts, statistics, medication names, techniques, or clinical "
    "findings (deliberately MORE than the {n} you will finally emit, so that weak or "
    "unverifiable candidates can be dropped in PASS 4 without shrinking the output). "
    "Each fact must be directly stated in the source text.\n\n"
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
    "PASS 4 — SOURCE-VERIFICATION FILTER (this decides what is emitted):\n"
    "Now audit your candidate pairs against the source ONE AT A TIME. Register "
    "translation (PASS 3) is allowed to change wording, but it must NOT have "
    "introduced any content the source does not state. For each candidate:\n"
    "- Take every distinct claim the answer makes — each stated cause, reason, "
    "motivation, driver, number, name, list item, and cause->effect link — and find "
    "the exact source sentence that states it. Silently quote that sentence to "
    "yourself.\n"
    "- If ANY claim cannot be traced to an explicit source sentence — this INCLUDES "
    "plausible-sounding lists of reasons, causes, or motivations that the source "
    "never actually gives (e.g. answering 'why do teens start smoking' with "
    "'peer pressure, curiosity, fitting in' when the source names none of those) — "
    "the pair is UNVERIFIED. DISCARD it entirely. Do NOT soften, hedge, or repair "
    "it into a partial answer; drop the whole pair.\n"
    "- A pair survives ONLY if 100% of its answer's content is source-supported.\n"
    "Then emit the surviving pairs, choosing the {n} best-grounded and most distinct "
    "ones. If fewer than {n} pairs survive verification, emit ONLY those that "
    "survived — it is correct and REQUIRED to return fewer than {n} pairs rather "
    "than emit a single unverified or invented pair to hit the count.\n\n"
    "RULES:\n"
    "1. Every fact in every answer must trace to a specific sentence in the source; "
    "only the wording is translated, never the clinical content.\n"
    "2. Warmth and direct address are TONE, not information — never introduce a "
    "fact, reassurance, or claim the source does not support.\n"
    "3. Cover {n} DIFFERENT topics — no repeated themes.\n"
    "4. No disclaimers, hedging, or generic advice unless the source says it.\n"
    "5. If fewer than {n} candidates survive PASS-4 verification, emit fewer pairs. "
    "Never pad the count with an unverified pair.\n\n"
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
