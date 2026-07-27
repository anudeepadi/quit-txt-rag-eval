"""QuitTxt Data-Generation Autoresearch — Fixed infrastructure.

NOT modified by the agent. Provides:
  - Source content loading (real web pages + human KB reference)
  - QA generation from source content
  - Evaluation via RAG pipeline (ChromaDB + LLM-as-judge)
  - Head-to-head comparison against human-curated KB
  - Results logging

The scoring pipeline:
  1. Agent generates QA pairs using its prompt (from data_gen_experiment.py)
  2. Those pairs are loaded into a ChromaDB collection
  3. The same 20 test questions are answered using that collection
  4. LLM-as-judge scores faithfulness of each answer
  5. BONUS: a separate quality judge scores the QA pairs directly
     (specificity, conversational tone, clinical accuracy)
  6. Combined score determines if the generation prompt improved
"""

import json
import os
import random
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_CODE_ROOT = Path(__file__).parent.parent  # gemini-protocol/code/
_PROJECT_ROOT = _CODE_ROOT.parent          # gemini-protocol/
_AUTORESEARCH_DIR = Path(__file__).parent

# .env loading
_ENV_PATH = _CODE_ROOT / ".env"
if not _ENV_PATH.exists():
    _ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Add it to code/.env or export it.")

# ---------------------------------------------------------------------------
# Dataset paths (direct, no broken loaders)
# ---------------------------------------------------------------------------
HUMAN_KB_PATH = _PROJECT_ROOT / "datasets" / "human-rag" / "human_curated_qa.jsonl"
AI_KB_PATH = _PROJECT_ROOT / "datasets" / "human-ai" / "ai_generated_qa.jsonl"
WEB_KB_PATH = _PROJECT_ROOT / "datasets" / "eval-rag" / "web_scraped_qa.jsonl"
WEB_SOURCE_CORPUS_PATH = _PROJECT_ROOT / "datasets" / "eval-rag" / "web_source_documents.jsonl"
TEST_SET_PATH = _PROJECT_ROOT / "datasets" / "eval-rag" / "test_set_150q.xlsx"

RESULTS_FILE = _AUTORESEARCH_DIR / "data_gen_results.tsv"
# Superseded by the dev/test freeze: the loop now scores against the full DEV
# split (shared.question_split.load_dev_questions), not a fixed 20-row slice of
# the test sheet. Kept only so older result rows remain interpretable.
N_EVAL = 20
N_SOURCE_CHUNKS = 10**9  # all chunks (source parity with human arm; epoch 3)
RANDOM_SEED = 42         # deterministic source selection

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import chromadb
from chromadb.config import Settings
from openai import OpenAI

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    """Load QA pairs from a JSONL file."""
    pairs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def load_human_kb() -> list[dict]:
    """Load the human-curated knowledge base (gold standard)."""
    return load_jsonl(HUMAN_KB_PATH)


def load_test_questions(max_rows: int | None = None) -> list[dict]:
    """Load the DEV questions the optimization loop is allowed to score against.

    Previously this read ``rows[:20]`` straight off the 150-question sheet, so
    every experiment was scored on the same 20 questions that later appeared in
    the reported test set (16 of them survived clinical filtering into the
    evaluated 100). That made the headline number partly a measure of fit to
    those items. See ``shared.question_split`` for the freeze.

    The dev set is fixed rather than resampled per experiment: KEEP/DISCARD
    compares scores across experiments, so the question set must be constant or
    the comparison is noise.

    Args:
        max_rows: Optionally cap the dev questions used. Defaults to all of them.

    Returns:
        Dicts with 'question' and 'reference_answer', matching the previous shape.
    """
    sys.path.insert(0, str(_CODE_ROOT))
    from shared.question_split import load_dev_questions

    dev = load_dev_questions()
    if max_rows is not None:
        dev = dev[:max_rows]
    return [
        {"question": q.question, "reference_answer": q.ground_truth}
        for q in dev
    ]


# Retained for reference only. Deliberately NOT used as a fallback: silently
# swapping in a different question set would make scores incomparable across
# experiments, and these paraphrase real test items.
_FALLBACK_QUESTIONS = [
    {"question": "What medications can help me quit smoking?", "reference_answer": ""},
    {"question": "How do I deal with nicotine withdrawal symptoms?", "reference_answer": ""},
    {"question": "Is vaping a safe alternative to smoking?", "reference_answer": ""},
    {"question": "What happens to my body after I quit smoking?", "reference_answer": ""},
    {"question": "How can I manage stress without cigarettes?", "reference_answer": ""},
    {"question": "What is nicotine replacement therapy?", "reference_answer": ""},
    {"question": "How long do withdrawal symptoms last?", "reference_answer": ""},
    {"question": "Can smoking cause cancer?", "reference_answer": ""},
    {"question": "What are the benefits of quitting smoking?", "reference_answer": ""},
    {"question": "How do I handle cravings when I want to quit?", "reference_answer": ""},
    {"question": "Is it too late to quit smoking at my age?", "reference_answer": ""},
    {"question": "What support groups are available for quitting?", "reference_answer": ""},
    {"question": "How does secondhand smoke affect my family?", "reference_answer": ""},
    {"question": "What are the side effects of nicotine patches?", "reference_answer": ""},
    {"question": "How much money will I save if I quit smoking?", "reference_answer": ""},
    {"question": "Can my doctor prescribe something to help me quit?", "reference_answer": ""},
    {"question": "What triggers make people want to smoke?", "reference_answer": ""},
    {"question": "How do I prepare for my quit date?", "reference_answer": ""},
    {"question": "Does exercise help with quitting smoking?", "reference_answer": ""},
    {"question": "What should I do if I relapse after quitting?", "reference_answer": ""},
]


# ---------------------------------------------------------------------------
# Source content for QA generation
# ---------------------------------------------------------------------------

def get_source_content_from_human_kb(n_chunks: int = N_SOURCE_CHUNKS) -> list[dict]:
    """Sample source content chunks from the human KB.

    We use actual human QA pairs grouped by topic as "source documents"
    that the generation prompt must work with. This lets us directly
    compare: given the SAME source material, does the AI-generated
    version match the human version?
    """
    human_pairs = load_human_kb()
    random.seed(RANDOM_SEED)

    # Group consecutive pairs into chunks of ~10 to simulate "page content"
    chunk_size = 10
    chunks = []
    for i in range(0, len(human_pairs), chunk_size):
        batch = human_pairs[i:i + chunk_size]
        # Build a "source document" from the answers (simulating web content)
        content = "\n\n".join(
            f"Topic: {p['question']}\n{p['answer']}" for p in batch
        )
        chunks.append({
            "content": content,
            "source": "human_kb",
            "ids": [p.get("id", f"hk_{i+j}") for j, p in enumerate(batch)],
            "reference_pairs": batch,  # ground truth for quality comparison
        })

    selected = random.sample(chunks, min(n_chunks, len(chunks)))
    return selected


def get_source_content_from_web(n_chunks: int = N_SOURCE_CHUNKS) -> list[dict]:
    """Sample persisted primary web-page text for non-circular generation.

    The corpus is created by ``build_web_dataset.py --source-only``.  We do
    not use the earlier LLM-generated web Q&A pairs here: doing so would make
    this arm a rephrasing experiment rather than web-source generation.
    """
    if not WEB_SOURCE_CORPUS_PATH.exists():
        raise FileNotFoundError(
            f"Web source corpus is missing: {WEB_SOURCE_CORPUS_PATH}. Run "
            "python code/scripts/build_web_dataset.py --source-only first."
        )

    documents = load_jsonl(WEB_SOURCE_CORPUS_PATH)
    random.seed(RANDOM_SEED)
    valid_documents = [
        document for document in documents
        if isinstance(document.get("url"), str) and isinstance(document.get("content"), str)
    ]
    if not valid_documents:
        raise ValueError(f"No usable source documents in {WEB_SOURCE_CORPUS_PATH}")

    return random.sample(valid_documents, min(n_chunks, len(valid_documents)))


# ---------------------------------------------------------------------------
# QA Generation
# ---------------------------------------------------------------------------

def generate_qa_pairs(
    oai_client: OpenAI,
    source_content: str,
    system_prompt: str,
    n_pairs: int,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 2500,
    stats: dict | None = None,
) -> list[dict]:
    """Generate QA pairs from source content using the given prompt.

    Args:
        stats: Optional mutable counters for the dataset manifest
            (dataset-generation protocol A1). When given, increments
            "n_raw" per parsed candidate pair and "n_rejected_wellformed"
            per candidate dropped by the length filter. Counting only —
            the filter itself is unchanged.
    """
    formatted_prompt = system_prompt.format(n=n_pairs)

    try:
        resp = oai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": f"Source content:\n\n{source_content}"},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        raw = json.loads(resp.choices[0].message.content)
        pairs = (
            raw if isinstance(raw, list)
            else raw.get("qa_pairs", raw.get("pairs", raw.get("questions", [])))
        )

        result = []
        for p in pairs:
            q = str(p.get("question", "")).strip()
            a = str(p.get("answer", "")).strip()
            if stats is not None:
                stats["n_raw"] = stats.get("n_raw", 0) + 1
            if len(q) > 10 and len(a) > 20:
                result.append({"question": q, "answer": a})
            elif stats is not None:
                stats["n_rejected_wellformed"] = stats.get("n_rejected_wellformed", 0) + 1
        return result

    except Exception as e:
        print(f"  GENERATION ERROR: {e}")
        return []


# ---------------------------------------------------------------------------
# ChromaDB collection builder
# ---------------------------------------------------------------------------

def build_collection(
    chroma_client: chromadb.Client,
    name: str,
    qa_pairs: list[dict],
) -> chromadb.Collection:
    """Build ephemeral ChromaDB collection from QA pairs."""
    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 100
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i:i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [f"{name}_{i + j}" for j, p in enumerate(batch)]
        collection.add(documents=documents, ids=ids)

    return collection


# ---------------------------------------------------------------------------
# Faithfulness scoring (LLM-as-judge) — reused from existing autoresearch
# ---------------------------------------------------------------------------

_FAITHFULNESS_PROMPT = """Rate how well the Response is grounded in the Context.

Scale:
0 = Response is entirely fabricated, nothing from Context
3 = Mostly fabricated with a few grounded facts
5 = Mix of grounded and fabricated information
7 = Mostly grounded with minor unsupported additions
10 = Every claim in Response is directly supported by Context

Context:
{context}

Question: {question}

Response: {response}

Score (just the number, nothing else):"""


# Refusal answers ("the knowledge base does not provide...") contain no claims,
# so the grounding rubric is vacuously satisfiable and the judge oscillates
# between 0 and 10 on near-identical text (verified epoch-1 nondeterminism).
# For this metric's purpose — does the KB support answering the question? —
# a refusal is a KB failure: score 0.0 deterministically, both arms.
_REFUSAL_RE = re.compile(
    r"(?:knowledge base|context|source|provided information)[^.]{0,60}?"
    r"(?:does not|doesn't|do not|don't)\s+"
    r"(?:provide|contain|include|cover|mention|address|offer|have)"
    r"|no (?:specific )?information (?:is )?(?:available|provided)",
    re.IGNORECASE,
)


def _is_refusal(response: str) -> bool:
    """True when the answer's first sentence declines to answer."""
    first_sentence = response.split(".", 1)[0]
    return bool(_REFUSAL_RE.search(first_sentence))


def score_faithfulness(
    oai_client: OpenAI,
    question: str,
    response: str,
    contexts: list[str],
) -> float:
    """Fast faithfulness proxy using LLM-as-judge. Returns 0.0–1.0."""
    if _is_refusal(response):
        return 0.0
    context_text = "\n\n".join(contexts) if contexts else "(no context)"
    try:
        result = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": _FAITHFULNESS_PROMPT.format(
                    context=context_text, question=question, response=response,
                )},
            ],
            temperature=0.0,
            max_tokens=5,
        )
        raw = result.choices[0].message.content.strip()
        score = float("".join(c for c in raw if c.isdigit() or c == "."))
        return min(max(score / 10.0, 0.0), 1.0)
    except Exception:
        return 0.5


# ---------------------------------------------------------------------------
# QA Quality scoring — rates the generated pairs themselves
# ---------------------------------------------------------------------------

_QA_QUALITY_PROMPT = """You are evaluating AI-generated Q&A training data for a smoking cessation chatbot.

Rate this Q&A pair on these criteria (each 0-10):

1. SPECIFICITY: Does the answer contain concrete facts (medications, dosages, timeframes, percentages, named techniques)?
   0 = completely generic ("talk to your doctor")
   10 = highly specific ("Varenicline (Chantix) reduces cravings by blocking nicotinic receptors; typical course is 12 weeks starting 1 week before quit date")

2. CONVERSATIONAL_TONE: Does the question sound like a real person texting a quit-smoking chatbot?
   0 = formal/clinical ("What are the pharmacological interventions for nicotine dependence?")
   10 = natural ("I keep reaching for a smoke when I'm stressed - what else can I do?")

3. GROUNDEDNESS: Is the answer faithful to the source content provided, with no fabricated claims?
   0 = entirely fabricated
   10 = every claim traceable to source

4. CLINICAL_ACCURACY: Would a cessation counselor agree this is correct and helpful advice?
   0 = dangerously wrong
   10 = clinically sound and actionable

Source content:
{source}

Question: {question}
Answer: {answer}

Return ONLY a JSON object: {{"specificity": N, "conversational_tone": N, "groundedness": N, "clinical_accuracy": N}}"""


def score_qa_quality(
    oai_client: OpenAI,
    question: str,
    answer: str,
    source_content: str,
) -> dict:
    """Score a single QA pair on 4 quality dimensions. Returns dict of 0-1 scores."""
    try:
        result = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": _QA_QUALITY_PROMPT.format(
                    source=source_content[:3000],
                    question=question,
                    answer=answer,
                )},
            ],
            temperature=0.0,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        raw = json.loads(result.choices[0].message.content)
        return {
            k: min(max(float(raw.get(k, 5)) / 10.0, 0.0), 1.0)
            for k in ["specificity", "conversational_tone", "groundedness", "clinical_accuracy"]
        }
    except Exception as e:
        print(f"  QA QUALITY SCORING ERROR: {e}")
        return {k: 0.5 for k in ["specificity", "conversational_tone", "groundedness", "clinical_accuracy"]}


# ---------------------------------------------------------------------------
# Human KB baseline scoring (for head-to-head comparison)
# ---------------------------------------------------------------------------

def score_human_baseline(
    oai_client: OpenAI,
    chroma_client: chromadb.Client,
    test_questions: list[dict],
    rag_template: str,
    rag_temperature: float,
    rag_max_tokens: int,
    rag_top_k: int,
) -> float:
    """Run the same RAG eval using the human KB. Returns avg faithfulness."""
    human_pairs = load_human_kb()
    collection = build_collection(chroma_client, "human_baseline", human_pairs)

    scores = []
    for row in test_questions:
        question = row["question"]
        results = collection.query(query_texts=[question], n_results=rag_top_k)
        contexts = results["documents"][0] if results["documents"] and results["documents"][0] else []

        knowledge = "\n\n".join(contexts)
        system_prompt = rag_template.format(knowledge=knowledge)

        try:
            response = oai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=rag_temperature,
                max_tokens=rag_max_tokens,
            )
            answer = response.choices[0].message.content.strip()
        except Exception:
            answer = ""

        if answer:
            score = score_faithfulness(oai_client, question, answer, contexts)
            scores.append(score)
        else:
            scores.append(0.0)

    return sum(scores) / len(scores) if scores else 0.0


# ---------------------------------------------------------------------------
# Results log
# ---------------------------------------------------------------------------

_TSV_HEADER = (
    "exp_id\ttimestamp\thypothesis\tgen_model\t"
    "rag_faithfulness\tqa_specificity\tqa_tone\tqa_groundedness\tqa_clinical\t"
    "combined_score\thuman_baseline\trelative_pct\t"
    "n_pairs_generated\tavg_answer_words\t"
    "gen_temperature\tgen_max_tokens\tqa_per_source\tverdict\n"
)


def get_best_score() -> float:
    """Read best combined_score from data_gen_results.tsv."""
    if not RESULTS_FILE.exists():
        return 0.0
    best = 0.0
    with open(RESULTS_FILE) as f:
        for line in f:
            if line.startswith("exp_id") or line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 10:
                try:
                    score = float(parts[9])  # combined_score column
                    if score > best:
                        best = score
                except ValueError:
                    pass
    return best


def get_experiment_count() -> int:
    """Count existing experiments."""
    if not RESULTS_FILE.exists():
        return 0
    count = 0
    with open(RESULTS_FILE) as f:
        for line in f:
            if not line.startswith("exp_id") and not line.startswith("#") and line.strip():
                count += 1
    return count


def log_result(
    experiment_id: int,
    hypothesis: str,
    gen_model: str,
    rag_faithfulness: float,
    qa_quality: dict,
    combined_score: float,
    human_baseline: float,
    relative_pct: float,
    n_pairs: int,
    avg_answer_words: float,
    gen_temperature: float,
    gen_max_tokens: int,
    qa_per_source: int,
    verdict: str,
) -> None:
    """Append one result row to data_gen_results.tsv."""
    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, "w") as f:
            f.write(_TSV_HEADER)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = (
        f"{experiment_id}\t{timestamp}\t{hypothesis}\t{gen_model}\t"
        f"{rag_faithfulness:.4f}\t"
        f"{qa_quality.get('specificity', 0):.4f}\t"
        f"{qa_quality.get('conversational_tone', 0):.4f}\t"
        f"{qa_quality.get('groundedness', 0):.4f}\t"
        f"{qa_quality.get('clinical_accuracy', 0):.4f}\t"
        f"{combined_score:.4f}\t{human_baseline:.4f}\t{relative_pct:.1f}\t"
        f"{n_pairs}\t{avg_answer_words:.1f}\t"
        f"{gen_temperature}\t{gen_max_tokens}\t{qa_per_source}\t{verdict}\n"
    )
    with open(RESULTS_FILE, "a") as f:
        f.write(row)


# ---------------------------------------------------------------------------
# Validation (run directly)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Data-Generation Autoresearch — Environment Validation")
    print("=" * 60)

    print(f"\nOpenAI API key: {'set' if OPENAI_API_KEY else 'MISSING'}")
    print(f"Human KB: {HUMAN_KB_PATH} ({'exists' if HUMAN_KB_PATH.exists() else 'MISSING'})")
    print(f"AI KB: {AI_KB_PATH} ({'exists' if AI_KB_PATH.exists() else 'MISSING'})")
    print(f"Web KB: {WEB_KB_PATH} ({'exists' if WEB_KB_PATH.exists() else 'MISSING'})")
    print(f"Test set: {TEST_SET_PATH} ({'exists' if TEST_SET_PATH.exists() else 'MISSING'})")

    print("\nLoading datasets...")
    h = load_human_kb()
    print(f"  Human KB: {len(h):,} pairs")

    print("\nLoading test questions...")
    tq = load_test_questions()
    print(f"  {len(tq)} questions loaded")

    print("\nLoading source content chunks...")
    chunks = get_source_content_from_human_kb()
    print(f"  {len(chunks)} chunks, ~{sum(len(c['content']) for c in chunks)} chars total")

    print("\nQuick API test...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'ok' and nothing else."}],
            max_tokens=5,
        )
        print(f"  API response: {r.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  API ERROR: {e}")

    print(f"\nResults file: {RESULTS_FILE}")
    print(f"  Existing experiments: {get_experiment_count()}")
    print(f"  Best score: {get_best_score():.4f}")

    print("\n✓ Validation complete. Ready for data-generation autoresearch.")
