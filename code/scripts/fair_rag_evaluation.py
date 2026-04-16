#!/usr/bin/env python3
"""Fair RAG Evaluation: Baseline vs AI-Generated vs Human-Curated.

This script uses proper semantic search (ChromaDB with embeddings) to fairly
compare three configurations:
1. Baseline (No RAG) - LLM only
2. AI-Generated RAG - Retrieval from AI-generated dataset
3. Human-Curated RAG - Retrieval from human-curated dataset

Goal: Prove the hierarchy: Baseline < AI-Generated < Human-Curated

Usage:
    python scripts/fair_rag_evaluation.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
ENV_PATH = Path(__file__).parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

from openai import OpenAI
import chromadb
from chromadb.config import Settings
from sacrebleu.metrics import BLEU
from rouge_score import rouge_scorer

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "final_paper_results"

# Model settings
MODEL_NAME = "gpt-4o-mini"  # Fast and cost-effective
TEMPERATURE = 0.3
MAX_TOKENS = 300

# Test questions with reference answers (held-out, not from either dataset)
TEST_DATA = [
    {
        "question": "I've been smoking for 20 years. Is it too late for me to quit?",
        "reference": "It's never too late to quit smoking. Even after 20 years, your body can begin to heal. Within 20 minutes of quitting, your heart rate drops. Within 12 hours, carbon monoxide levels normalize. Long-term benefits include reduced risk of heart disease and cancer.",
    },
    {
        "question": "What happens to my body in the first 24 hours after I quit smoking?",
        "reference": "In the first 24 hours: Within 20 minutes, heart rate and blood pressure drop. At 8 hours, carbon monoxide levels decrease. At 24 hours, your risk of heart attack begins to decrease. You may experience withdrawal symptoms like irritability and cravings.",
    },
    {
        "question": "How can I deal with nicotine cravings when they hit?",
        "reference": "To manage cravings, try the 4 Ds: Delay acting on the craving, Deep breathe, Drink water, and Do something else. Cravings typically last 3-5 minutes. Physical activity, chewing gum, or calling a support person can also help.",
    },
    {
        "question": "What are the best nicotine replacement therapy options?",
        "reference": "NRT options include patches (steady nicotine release), gum (as-needed relief), lozenges, inhalers, and nasal sprays. Patches are good for constant cravings, while gum and lozenges help sudden urges. Combining methods can be more effective.",
    },
    {
        "question": "Will I gain weight if I quit smoking?",
        "reference": "Some weight gain is common (5-10 pounds) because nicotine suppresses appetite and increases metabolism. To minimize gain: exercise regularly, choose healthy snacks, drink water, and don't use food to replace smoking. Health benefits of quitting outweigh weight concerns.",
    },
    {
        "question": "How does smoking affect my cardiovascular health?",
        "reference": "Smoking damages blood vessels, raises blood pressure, reduces oxygen in blood, and increases heart rate. It significantly increases risk of heart attack, stroke, and peripheral artery disease. Quitting can rapidly reduce these risks.",
    },
    {
        "question": "What should I do if I relapse after quitting?",
        "reference": "A slip doesn't mean failure. Don't give up - most successful quitters try multiple times. Identify what triggered the relapse, learn from it, and recommit immediately. Consider adjusting your quit strategy or seeking additional support.",
    },
    {
        "question": "Can you explain how nicotine addiction works in the brain?",
        "reference": "Nicotine reaches the brain within seconds, triggering dopamine release that creates pleasure. Over time, the brain develops tolerance and needs more nicotine. Withdrawal occurs when nicotine levels drop, causing cravings, irritability, and difficulty concentrating.",
    },
    {
        "question": "What are the benefits of quitting smoking after 1 year?",
        "reference": "After 1 year smoke-free: heart disease risk drops by half compared to smokers, lung function improves, circulation is better, energy levels increase, and risk of various cancers decreases. Coughing and shortness of breath continue to improve.",
    },
    {
        "question": "How can I help a family member who wants to quit smoking?",
        "reference": "Be supportive without nagging. Offer encouragement, celebrate milestones, help identify triggers, join smoke-free activities together. Don't criticize slips. Help create a smoke-free environment and be patient - quitting is difficult.",
    },
    {
        "question": "What medications can help with smoking cessation?",
        "reference": "Prescription options include Varenicline (Chantix) which blocks nicotine receptors and reduces cravings, and Bupropion (Wellbutrin/Zyban) which reduces withdrawal symptoms. Both can double quit success rates when combined with counseling.",
    },
    {
        "question": "How does secondhand smoke affect children?",
        "reference": "Children exposed to secondhand smoke have higher rates of ear infections, asthma, respiratory infections, and sudden infant death syndrome (SIDS). Their developing lungs are especially vulnerable. Never smoke indoors or in cars with children.",
    },
    {
        "question": "What triggers should I avoid when trying to quit?",
        "reference": "Common triggers include alcohol, coffee, stress, other smokers, and specific routines. Avoid or plan for these situations. Change routines, limit alcohol initially, find new ways to handle stress, and ask smoking friends to support your quit.",
    },
    {
        "question": "How long do withdrawal symptoms typically last?",
        "reference": "Most physical withdrawal symptoms peak within 2-3 days and subside within 2-4 weeks. Psychological cravings may persist longer but become less frequent. Irritability, difficulty concentrating, and sleep issues are common but temporary.",
    },
    {
        "question": "Is cold turkey or gradual reduction better for quitting?",
        "reference": "Both methods can work. Cold turkey works for some who prefer a clean break. Gradual reduction can ease withdrawal. Research suggests setting a quit date and stopping completely often has better long-term success than cutting down slowly.",
    },
]


def load_human_curated() -> List[Dict]:
    """Load human-curated QA dataset from JSONL."""
    pairs = []
    path = DATA_DIR / "qa.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                # Ensure we have id field
                if "id" not in item:
                    item["id"] = f"human_{len(pairs)}"
                pairs.append(item)
    return pairs


def load_ai_generated() -> List[Dict]:
    """Load AI-generated QA dataset from JSONL."""
    pairs = []
    path = DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                # Ensure we have id field
                if "id" not in item:
                    item["id"] = f"ai_{len(pairs)}"
                pairs.append(item)
    return pairs


def create_collection(
    client: chromadb.Client, name: str, qa_pairs: List[Dict]
) -> chromadb.Collection:
    """Create a ChromaDB collection with proper embeddings."""
    # Delete if exists
    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

    # Add documents in batches
    batch_size = 100
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i:i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"doc_{i+j}")) for j, p in enumerate(batch)]
        metadatas = [{"question": p["question"], "answer": p["answer"]} for p in batch]

        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

    return collection


def retrieve_context(collection: chromadb.Collection, query: str, n_results: int = 3) -> str:
    """Retrieve relevant context using semantic search."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    contexts = []
    if results["documents"] and results["documents"][0]:
        for doc in results["documents"][0]:
            contexts.append(doc)

    return "\n\n".join(contexts)


def generate_baseline_response(question: str) -> str:
    """Generate response WITHOUT any RAG context (baseline)."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a compassionate smoking cessation counselor. Answer questions concisely (2-4 sentences)."},
                {"role": "user", "content": question}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def generate_rag_response(question: str, context: str) -> str:
    """Generate response WITH RAG context."""
    system_prompt = f"""You are a compassionate smoking cessation counselor.
Use the following knowledge base to answer questions.
Base your answer on the knowledge provided.

KNOWLEDGE BASE:
{context}"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def calculate_bleu(references: List[str], candidates: List[str]) -> float:
    """Calculate corpus-level BLEU score."""
    bleu = BLEU()
    score = bleu.corpus_score(candidates, [[r] for r in references])
    return score.score / 100  # Normalize to 0-1


def calculate_rouge(references: List[str], candidates: List[str]) -> Dict[str, float]:
    """Calculate average ROUGE scores."""
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = {"rouge1": [], "rouge2": [], "rougeL": []}

    for ref, cand in zip(references, candidates):
        result = scorer.score(ref, cand)
        scores["rouge1"].append(result["rouge1"].fmeasure)
        scores["rouge2"].append(result["rouge2"].fmeasure)
        scores["rougeL"].append(result["rougeL"].fmeasure)

    return {
        "rouge1": sum(scores["rouge1"]) / len(scores["rouge1"]),
        "rouge2": sum(scores["rouge2"]) / len(scores["rouge2"]),
        "rougeL": sum(scores["rougeL"]) / len(scores["rougeL"]),
    }


def run_evaluation():
    """Run the full fair evaluation."""
    print("=" * 70)
    print("FAIR RAG EVALUATION")
    print("Baseline vs AI-Generated vs Human-Curated")
    print("=" * 70)
    print()

    # Load datasets
    print("Loading datasets...")
    human_data = load_human_curated()
    ai_data = load_ai_generated()
    print(f"  Human-curated: {len(human_data):,} pairs")
    print(f"  AI-generated:  {len(ai_data):,} pairs")
    print()

    # Create ChromaDB collections
    print("Creating ChromaDB collections with embeddings...")
    client = chromadb.Client(Settings(anonymized_telemetry=False))

    print("  Creating human-curated collection...")
    human_collection = create_collection(client, "human_curated", human_data)
    print(f"    Added {human_collection.count()} documents")

    print("  Creating AI-generated collection...")
    ai_collection = create_collection(client, "ai_generated", ai_data)
    print(f"    Added {ai_collection.count()} documents")
    print()

    # Run evaluation
    results = {
        "baseline": {"responses": [], "references": []},
        "ai_rag": {"responses": [], "references": []},
        "human_rag": {"responses": [], "references": []},
    }

    print(f"Evaluating {len(TEST_DATA)} test questions...")
    print("-" * 70)

    for i, test in enumerate(TEST_DATA, 1):
        question = test["question"]
        reference = test["reference"]

        print(f"\n[{i}/{len(TEST_DATA)}] {question[:50]}...")

        # 1. Baseline (No RAG)
        baseline_response = generate_baseline_response(question)
        results["baseline"]["responses"].append(baseline_response)
        results["baseline"]["references"].append(reference)
        time.sleep(0.3)

        # 2. AI-Generated RAG
        ai_context = retrieve_context(ai_collection, question)
        ai_response = generate_rag_response(question, ai_context)
        results["ai_rag"]["responses"].append(ai_response)
        results["ai_rag"]["references"].append(reference)
        time.sleep(0.3)

        # 3. Human-Curated RAG
        human_context = retrieve_context(human_collection, question)
        human_response = generate_rag_response(question, human_context)
        results["human_rag"]["responses"].append(human_response)
        results["human_rag"]["references"].append(reference)
        time.sleep(0.3)

        print(f"  Baseline: {len(baseline_response)} chars")
        print(f"  AI RAG:   {len(ai_response)} chars")
        print(f"  Human RAG: {len(human_response)} chars")

    # Compute metrics
    print()
    print("=" * 70)
    print("COMPUTING METRICS")
    print("=" * 70)

    metrics = {}
    for config_name, data in results.items():
        bleu = calculate_bleu(data["references"], data["responses"])
        rouge = calculate_rouge(data["references"], data["responses"])
        metrics[config_name] = {
            "bleu": bleu,
            "rouge1": rouge["rouge1"],
            "rouge2": rouge["rouge2"],
            "rougeL": rouge["rougeL"],
        }

    # Print results table
    print()
    print(f"{'Configuration':<20} {'BLEU':>10} {'ROUGE-1':>10} {'ROUGE-2':>10} {'ROUGE-L':>10}")
    print("-" * 65)
    for config_name, m in metrics.items():
        label = config_name.replace("_", " ").title()
        print(f"{label:<20} {m['bleu']:>10.4f} {m['rouge1']:>10.4f} {m['rouge2']:>10.4f} {m['rougeL']:>10.4f}")

    # Check hierarchy
    print()
    print("=" * 70)
    print("HIERARCHY CHECK: Baseline < AI-Generated < Human-Curated")
    print("=" * 70)

    baseline_bleu = metrics["baseline"]["bleu"]
    ai_bleu = metrics["ai_rag"]["bleu"]
    human_bleu = metrics["human_rag"]["bleu"]

    baseline_rouge = metrics["baseline"]["rougeL"]
    ai_rouge = metrics["ai_rag"]["rougeL"]
    human_rouge = metrics["human_rag"]["rougeL"]

    # BLEU hierarchy
    if baseline_bleu < ai_bleu < human_bleu:
        print("BLEU:    Baseline < AI < Human")
    elif baseline_bleu < ai_bleu:
        print("BLEU:    Baseline < AI (Human not highest)")
    elif ai_bleu < human_bleu:
        print("BLEU:    AI < Human (Baseline not lowest)")
    else:
        print(f"BLEU:    Unexpected order - Baseline={baseline_bleu:.4f}, AI={ai_bleu:.4f}, Human={human_bleu:.4f}")

    # ROUGE-L hierarchy
    if baseline_rouge < ai_rouge < human_rouge:
        print("ROUGE-L: Baseline < AI < Human")
    elif baseline_rouge < ai_rouge:
        print("ROUGE-L: Baseline < AI (Human not highest)")
    elif ai_rouge < human_rouge:
        print("ROUGE-L: AI < Human (Baseline not lowest)")
    else:
        print(f"ROUGE-L: Unexpected order - Baseline={baseline_rouge:.4f}, AI={ai_rouge:.4f}, Human={human_rouge:.4f}")

    # Improvement calculations
    print()
    print("IMPROVEMENTS:")
    if baseline_bleu > 0:
        ai_vs_baseline_bleu = ((ai_bleu - baseline_bleu) / baseline_bleu) * 100
        human_vs_baseline_bleu = ((human_bleu - baseline_bleu) / baseline_bleu) * 100
        print(f"  AI vs Baseline (BLEU):    {ai_vs_baseline_bleu:+.1f}%")
        print(f"  Human vs Baseline (BLEU): {human_vs_baseline_bleu:+.1f}%")

    if human_bleu > 0:
        ai_pct_of_human_bleu = (ai_bleu / human_bleu) * 100
        print(f"  AI achieves {ai_pct_of_human_bleu:.1f}% of Human (BLEU)")

    if human_rouge > 0:
        ai_pct_of_human_rouge = (ai_rouge / human_rouge) * 100
        print(f"  AI achieves {ai_pct_of_human_rouge:.1f}% of Human (ROUGE-L)")

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model": MODEL_NAME,
            "num_test_questions": len(TEST_DATA),
            "human_dataset_size": len(human_data),
            "ai_dataset_size": len(ai_data),
            "retrieval_method": "ChromaDB with default embeddings (cosine similarity)",
            "llm_provider": "OpenAI",
        },
        "metrics": metrics,
        "hierarchy_check": {
            "bleu_order": f"Baseline({baseline_bleu:.4f}) < AI({ai_bleu:.4f}) < Human({human_bleu:.4f})"
            if baseline_bleu < ai_bleu < human_bleu
            else f"Baseline({baseline_bleu:.4f}), AI({ai_bleu:.4f}), Human({human_bleu:.4f})",
            "rougeL_order": f"Baseline({baseline_rouge:.4f}) < AI({ai_rouge:.4f}) < Human({human_rouge:.4f})"
            if baseline_rouge < ai_rouge < human_rouge
            else f"Baseline({baseline_rouge:.4f}), AI({ai_rouge:.4f}), Human({human_rouge:.4f})",
        },
        "improvements": {
            "ai_vs_baseline_bleu_pct": ((ai_bleu - baseline_bleu) / baseline_bleu * 100) if baseline_bleu > 0 else None,
            "human_vs_baseline_bleu_pct": ((human_bleu - baseline_bleu) / baseline_bleu * 100) if baseline_bleu > 0 else None,
            "ai_pct_of_human_bleu": (ai_bleu / human_bleu * 100) if human_bleu > 0 else None,
            "ai_pct_of_human_rougeL": (ai_rouge / human_rouge * 100) if human_rouge > 0 else None,
        },
        "detailed_results": {
            config: {
                "responses": data["responses"],
                "references": data["references"],
            }
            for config, data in results.items()
        },
    }

    output_path = RESULTS_DIR / f"fair_rag_evaluation_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 70)
    print(f"Results saved to: {output_path}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    run_evaluation()
