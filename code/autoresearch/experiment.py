"""QuitTxt Autoresearch — Experiment Configuration.

THE AGENT MODIFIES THIS FILE. Everything else is fixed infrastructure.
After modifying, run:  python3 autoresearch/run_experiment.py
"""

# --- Hypothesis (describe what you're testing) ---
HYPOTHESIS = "Baseline concise config from manual experimentation"

# --- Target RAG config ---
# Options: "ai_rag", "human_rag", "web_rag"
TARGET_CONFIG = "human_rag"

# --- Generation parameters ---
TEMPERATURE = 0.3
MAX_TOKENS = 150
TOP_K = 3

# --- RAG template ---
# Must contain {knowledge} placeholder for retrieved context.
RAG_TEMPLATE = (
    "You are a smoking cessation counselor.\n"
    "Answer the question in 2-3 sentences using ONLY facts from the "
    "knowledge base below.\n"
    "Do NOT add information, examples, or details not explicitly stated "
    "in the knowledge base.\n\n"
    "KNOWLEDGE BASE:\n{knowledge}"
)
