#!/usr/bin/env python3
"""Three-Way Fair RAG Comparison.

Compares ALL THREE approaches under IDENTICAL conditions:
1. Web RAG (raw sources) - simulated with source excerpts
2. AI-Generated Dataset RAG
3. Human-Curated Dataset RAG

ALL use:
- Same 15 test questions
- Same LLM (GPT-4o-mini)
- Same ChromaDB retrieval
- Same evaluation metrics

This ensures a VALID comparison.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Load environment variables
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
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
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Same 15 test questions for ALL approaches
TEST_DATA = [
    {
        "question": "I've been smoking for 20 years. Is it too late for me to quit?",
        "reference": "It's never too late to quit smoking. Even after 20 years, your body can begin to heal. Within 20 minutes of quitting, your heart rate drops. Within 12 hours, carbon monoxide levels normalize.",
    },
    {
        "question": "What happens to my body in the first 24 hours after I quit smoking?",
        "reference": "In the first 24 hours: Within 20 minutes, heart rate and blood pressure drop. At 8 hours, carbon monoxide levels decrease. At 24 hours, your risk of heart attack begins to decrease.",
    },
    {
        "question": "How can I deal with nicotine cravings when they hit?",
        "reference": "To manage cravings, try the 4 Ds: Delay acting on the craving, Deep breathe, Drink water, and Do something else. Cravings typically last 3-5 minutes.",
    },
    {
        "question": "What are the best nicotine replacement therapy options?",
        "reference": "NRT options include patches, gum, lozenges, inhalers, and nasal sprays. Patches provide steady nicotine release, while gum and lozenges help sudden urges.",
    },
    {
        "question": "Will I gain weight if I quit smoking?",
        "reference": "Some weight gain is common (5-10 pounds) because nicotine suppresses appetite. To minimize gain: exercise regularly, choose healthy snacks, drink water.",
    },
    {
        "question": "How does smoking affect my cardiovascular health?",
        "reference": "Smoking damages blood vessels, raises blood pressure, reduces oxygen in blood, and increases heart rate. It significantly increases risk of heart attack and stroke.",
    },
    {
        "question": "What should I do if I relapse after quitting?",
        "reference": "A slip doesn't mean failure. Most successful quitters try multiple times. Identify what triggered the relapse, learn from it, and recommit immediately.",
    },
    {
        "question": "Can you explain how nicotine addiction works in the brain?",
        "reference": "Nicotine reaches the brain within seconds, triggering dopamine release. Over time, the brain develops tolerance and needs more nicotine. Withdrawal causes cravings.",
    },
    {
        "question": "What are the benefits of quitting smoking after 1 year?",
        "reference": "After 1 year: heart disease risk drops by half, lung function improves, circulation is better, and risk of various cancers decreases.",
    },
    {
        "question": "How can I help a family member who wants to quit smoking?",
        "reference": "Be supportive without nagging. Offer encouragement, celebrate milestones, help identify triggers. Don't criticize slips. Be patient.",
    },
    {
        "question": "What medications can help with smoking cessation?",
        "reference": "Prescription options include Varenicline (Chantix) which blocks nicotine receptors, and Bupropion (Wellbutrin/Zyban) which reduces withdrawal symptoms.",
    },
    {
        "question": "How does secondhand smoke affect children?",
        "reference": "Children exposed to secondhand smoke have higher rates of ear infections, asthma, and respiratory infections. Never smoke indoors or in cars with children.",
    },
    {
        "question": "What triggers should I avoid when trying to quit?",
        "reference": "Common triggers include alcohol, coffee, stress, other smokers, and specific routines. Change routines, limit alcohol initially, find new stress management.",
    },
    {
        "question": "How long do withdrawal symptoms typically last?",
        "reference": "Most physical withdrawal symptoms peak within 2-3 days and subside within 2-4 weeks. Psychological cravings may persist but become less frequent.",
    },
    {
        "question": "Is cold turkey or gradual reduction better for quitting?",
        "reference": "Both methods can work. Cold turkey works for some who prefer a clean break. Research suggests setting a quit date and stopping completely often has better success.",
    },
]

# Raw source content (simulating web RAG with actual source text)
RAW_SOURCES = """
Smoking cessation health benefits timeline:
- 20 minutes after quitting: Heart rate drops
- 12 hours: Carbon monoxide levels in blood drop to normal
- 2-12 weeks: Circulation improves and lung function increases
- 1-9 months: Coughing and shortness of breath decrease
- 1 year: Risk of coronary heart disease is half that of a smoker
- 5-15 years: Stroke risk is reduced to that of a nonsmoker

Nicotine replacement therapy (NRT) products include:
- Nicotine patches (provide steady dose)
- Nicotine gum (fast-acting, use when cravings hit)
- Nicotine lozenges (dissolve in mouth)
- Nicotine inhalers (prescription)
- Nicotine nasal spray (prescription)

Tips for managing cravings:
- Wait it out - cravings pass in 3-5 minutes
- Deep breathing exercises
- Drink water
- Distract yourself with activity
- Call a supportive friend

Weight gain after quitting:
Average weight gain is 5-10 pounds. Nicotine increases metabolism and suppresses appetite.
Combat this with regular exercise and healthy snacking.

Relapse prevention:
- Most people try to quit several times before succeeding
- A slip is not failure
- Learn from triggers
- Get back on track immediately

Secondhand smoke dangers:
Children exposed to secondhand smoke are at increased risk for:
- Sudden infant death syndrome (SIDS)
- Acute respiratory infections
- Ear problems
- More severe asthma
"""


def load_human_curated() -> List[Dict]:
    """Load human-curated QA dataset."""
    pairs = []
    path = DATA_DIR / "qa.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                if "id" not in item:
                    item["id"] = f"human_{len(pairs)}"
                pairs.append(item)
    return pairs


def load_ai_generated() -> List[Dict]:
    """Load AI-generated QA dataset."""
    pairs = []
    path = DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                if "id" not in item:
                    item["id"] = f"ai_{len(pairs)}"
                pairs.append(item)
    return pairs


def create_raw_source_collection(chroma_client) -> chromadb.Collection:
    """Create collection from raw source text (simulating web RAG)."""
    try:
        chroma_client.delete_collection("raw_sources")
    except:
        pass

    collection = chroma_client.create_collection(
        name="raw_sources",
        metadata={"hnsw:space": "cosine"}
    )

    # Split raw sources into chunks
    chunks = [chunk.strip() for chunk in RAW_SOURCES.split("\n\n") if chunk.strip()]

    collection.add(
        documents=chunks,
        ids=[f"raw_{i}" for i in range(len(chunks))],
        metadatas=[{"source": "raw_web"} for _ in chunks]
    )

    return collection


def create_qa_collection(chroma_client, name: str, qa_pairs: List[Dict]) -> chromadb.Collection:
    """Create collection from QA pairs."""
    try:
        chroma_client.delete_collection(name)
    except:
        pass

    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

    # Add in batches
    batch_size = 100
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i:i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"doc_{i+j}")) for j, p in enumerate(batch)]

        collection.add(documents=documents, ids=ids)

    return collection


def retrieve_context(collection: chromadb.Collection, query: str, n_results: int = 3) -> str:
    """Retrieve context using semantic search."""
    results = collection.query(query_texts=[query], n_results=n_results)

    if results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])
    return ""


def generate_response(question: str, context: str, is_baseline: bool = False) -> str:
    """Generate response using OpenAI."""
    if is_baseline:
        system_prompt = "You are a smoking cessation counselor. Answer concisely (2-3 sentences)."
        user_content = question
    else:
        system_prompt = f"""You are a smoking cessation counselor.
Use the following knowledge to answer questions concisely (2-3 sentences).

KNOWLEDGE:
{context}"""
        user_content = question

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def calculate_metrics(references: List[str], candidates: List[str]) -> Dict:
    """Calculate BLEU and ROUGE scores."""
    # BLEU
    bleu = BLEU()
    bleu_score = bleu.corpus_score(candidates, [[r] for r in references]).score / 100

    # ROUGE
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    rouge_scores = {"rouge1": [], "rouge2": [], "rougeL": []}

    for ref, cand in zip(references, candidates):
        result = scorer.score(ref, cand)
        rouge_scores["rouge1"].append(result["rouge1"].fmeasure)
        rouge_scores["rouge2"].append(result["rouge2"].fmeasure)
        rouge_scores["rougeL"].append(result["rougeL"].fmeasure)

    return {
        "bleu": bleu_score,
        "rouge1": sum(rouge_scores["rouge1"]) / len(rouge_scores["rouge1"]),
        "rouge2": sum(rouge_scores["rouge2"]) / len(rouge_scores["rouge2"]),
        "rougeL": sum(rouge_scores["rougeL"]) / len(rouge_scores["rougeL"]),
    }


def run_evaluation():
    """Run the three-way fair comparison."""
    print("=" * 70)
    print("THREE-WAY FAIR RAG COMPARISON")
    print("All approaches tested with IDENTICAL conditions")
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
    print("Creating ChromaDB collections...")
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

    raw_collection = create_raw_source_collection(chroma_client)
    print(f"  Raw sources: {raw_collection.count()} chunks")

    ai_collection = create_qa_collection(chroma_client, "ai_generated", ai_data)
    print(f"  AI-generated: {ai_collection.count()} documents")

    human_collection = create_qa_collection(chroma_client, "human_curated", human_data)
    print(f"  Human-curated: {human_collection.count()} documents")
    print()

    # Run evaluation
    results = {
        "baseline": {"responses": [], "references": []},
        "raw_rag": {"responses": [], "references": []},
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
        baseline_response = generate_response(question, "", is_baseline=True)
        results["baseline"]["responses"].append(baseline_response)
        results["baseline"]["references"].append(reference)
        time.sleep(0.3)

        # 2. Raw Sources RAG
        raw_context = retrieve_context(raw_collection, question)
        raw_response = generate_response(question, raw_context)
        results["raw_rag"]["responses"].append(raw_response)
        results["raw_rag"]["references"].append(reference)
        time.sleep(0.3)

        # 3. AI-Generated RAG
        ai_context = retrieve_context(ai_collection, question)
        ai_response = generate_response(question, ai_context)
        results["ai_rag"]["responses"].append(ai_response)
        results["ai_rag"]["references"].append(reference)
        time.sleep(0.3)

        # 4. Human-Curated RAG
        human_context = retrieve_context(human_collection, question)
        human_response = generate_response(question, human_context)
        results["human_rag"]["responses"].append(human_response)
        results["human_rag"]["references"].append(reference)
        time.sleep(0.3)

        print(f"  Baseline:  {len(baseline_response)} chars")
        print(f"  Raw RAG:   {len(raw_response)} chars")
        print(f"  AI RAG:    {len(ai_response)} chars")
        print(f"  Human RAG: {len(human_response)} chars")

    # Calculate metrics
    print()
    print("=" * 70)
    print("COMPUTING METRICS")
    print("=" * 70)

    metrics = {}
    for config_name, data in results.items():
        metrics[config_name] = calculate_metrics(data["references"], data["responses"])

    # Print results
    print()
    print(f"{'Configuration':<15} {'BLEU':>10} {'ROUGE-1':>10} {'ROUGE-L':>10}")
    print("-" * 50)
    for config_name, m in metrics.items():
        label = config_name.replace("_", " ").title()
        print(f"{label:<15} {m['bleu']:>10.4f} {m['rouge1']:>10.4f} {m['rougeL']:>10.4f}")

    # Calculate improvements
    print()
    print("=" * 70)
    print("IMPROVEMENT ANALYSIS")
    print("=" * 70)

    raw_bleu = metrics["raw_rag"]["bleu"]
    ai_bleu = metrics["ai_rag"]["bleu"]
    human_bleu = metrics["human_rag"]["bleu"]
    baseline_bleu = metrics["baseline"]["bleu"]

    print()
    print("vs Raw Sources (BLEU):")
    if raw_bleu > 0:
        ai_vs_raw = ((ai_bleu - raw_bleu) / raw_bleu) * 100
        human_vs_raw = ((human_bleu - raw_bleu) / raw_bleu) * 100
        print(f"  AI-Generated:   {ai_vs_raw:+.1f}%")
        print(f"  Human-Curated:  {human_vs_raw:+.1f}%")
    else:
        print("  Raw BLEU is 0, cannot calculate percentage")

    print()
    print("vs Human-Curated (BLEU):")
    if human_bleu > 0:
        ai_pct_human = (ai_bleu / human_bleu) * 100
        raw_pct_human = (raw_bleu / human_bleu) * 100
        print(f"  AI-Generated:   {ai_pct_human:.1f}%")
        print(f"  Raw Sources:    {raw_pct_human:.1f}%")

    # Hierarchy check
    print()
    print("HIERARCHY CHECK (Expected: Raw < AI < Human):")
    if raw_bleu < ai_bleu < human_bleu:
        print("  BLEU: Raw < AI < Human")
    else:
        print(f"  BLEU: Raw={raw_bleu:.4f}, AI={ai_bleu:.4f}, Human={human_bleu:.4f}")
        if ai_bleu > raw_bleu:
            print("  Partial: AI > Raw")
        if human_bleu > ai_bleu:
            print("  Partial: Human > AI")

    # Save results
    output_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model": MODEL_NAME,
            "num_test_questions": len(TEST_DATA),
            "human_dataset_size": len(human_data),
            "ai_dataset_size": len(ai_data),
            "method": "THREE-WAY FAIR COMPARISON - Same test questions for all approaches",
        },
        "metrics": metrics,
        "improvements": {
            "ai_vs_raw_bleu_pct": ((ai_bleu - raw_bleu) / raw_bleu * 100) if raw_bleu > 0 else None,
            "human_vs_raw_bleu_pct": ((human_bleu - raw_bleu) / raw_bleu * 100) if raw_bleu > 0 else None,
            "ai_pct_of_human_bleu": (ai_bleu / human_bleu * 100) if human_bleu > 0 else None,
            "raw_pct_of_human_bleu": (raw_bleu / human_bleu * 100) if human_bleu > 0 else None,
        },
        "detailed_results": {
            config: {"responses": data["responses"], "references": data["references"]}
            for config, data in results.items()
        },
    }

    output_path = output_dir / f"three_way_comparison_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 70)
    print(f"Results saved to: {output_path}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    run_evaluation()
