#!/usr/bin/env python3
"""
BERTScore vs ROUGE-L Comparison

Tests whether semantic similarity (BERTScore) shows different results
than textual similarity (ROUGE-L) for RAG evaluation.

Hypothesis: BERTScore should favor permissive prompts more than ROUGE-L
because it measures semantic meaning, not exact word overlap.

Author: Research Team
Date: January 2026
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings("ignore")

import numpy as np
from openai import OpenAI
import chromadb
from rouge_score import rouge_scorer

# Try to import BERTScore
try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
    print("✅ BERTScore available")
except ImportError:
    BERTSCORE_AVAILABLE = False
    print("❌ BERTScore not available - installing...")
    import subprocess
    subprocess.run(["pip", "install", "bert-score", "-q"])
    try:
        from bert_score import score as bert_score
        BERTSCORE_AVAILABLE = True
        print("✅ BERTScore installed successfully")
    except:
        print("❌ BERTScore installation failed")

# Load environment
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
class Config:
    MODEL_NAME = "gpt-4o-mini"
    TEMPERATURE = 0.3
    MAX_TOKENS = 300
    NUM_RETRIEVAL_DOCS = 3
    RESULTS_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent.parent.parent / "data"

config = Config()

# =============================================================================
# PROMPTS
# =============================================================================

CONSTRAINING_PROMPT = """You are a compassionate smoking cessation counselor. Use the provided context to answer. Be concise (2-4 sentences)."""

PERMISSIVE_PROMPT = """You are a compassionate smoking cessation counselor working with the QuitTxt program.

RESPONSE GUIDELINES:
1. Draw from the context below, but express strategies naturally in your own words
2. Be conversational - don't copy-paste, explain in a personalized way
3. Provide specifics - explain HOW to use techniques, not just that they exist
4. Be empathetic - acknowledge feelings before offering strategies
5. Keep responses substantive (3-5 sentences)

Use the context as a guide, but feel free to supplement with your knowledge for the best response."""


# =============================================================================
# METRICS
# =============================================================================

def compute_rouge_l(reference: str, candidate: str) -> float:
    """Compute ROUGE-L F1 score."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores['rougeL'].fmeasure


def compute_bertscore(references: List[str], candidates: List[str]) -> List[float]:
    """Compute BERTScore F1 for each pair."""
    if not BERTSCORE_AVAILABLE:
        return [0.0] * len(references)

    # Use a lighter model for speed
    P, R, F1 = bert_score(
        candidates, references,
        model_type="distilbert-base-uncased",
        batch_size=8,
        verbose=False
    )
    return F1.tolist()


# =============================================================================
# RESPONSE GENERATION
# =============================================================================

def generate_response(question: str, context: Optional[str], prompt_style: str) -> str:
    """Generate response with specified prompt style."""
    try:
        system_prompt = PERMISSIVE_PROMPT if prompt_style == "permissive" else CONSTRAINING_PROMPT

        if context:
            if prompt_style == "permissive":
                user_content = f"""=== RELEVANT CONTEXT ===
{context}

=== USER QUESTION ===
{question}

Please provide a helpful, personalized response."""
            else:
                user_content = f"Context:\n{context}\n\nQuestion: {question}"
        else:
            user_content = question

        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_bertscore_experiment(num_questions: int = 5) -> Dict:
    """Run BERTScore vs ROUGE-L comparison."""

    print("=" * 70)
    print("BERTScore vs ROUGE-L COMPARISON EXPERIMENT")
    print("=" * 70)
    print(f"\nHypothesis: BERTScore (semantic) should favor permissive prompts")
    print(f"            more than ROUGE-L (textual) does.\n")

    if not BERTSCORE_AVAILABLE:
        print("ERROR: BERTScore not available. Cannot run experiment.")
        return {}

    # Load data
    test_file = config.RESULTS_DIR / "FINAL_independent_test_set.json"
    with open(test_file) as f:
        test_data = json.load(f)['test_data'][:num_questions]

    ai_path = config.DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl"
    ai_data = []
    with open(ai_path) as f:
        for line in f:
            if line.strip():
                ai_data.append(json.loads(line))

    print(f"Test questions: {num_questions}")
    print(f"AI QA pairs: {len(ai_data)}")

    # Create ChromaDB collection
    print("\nCreating ChromaDB collection...")
    chroma_client = chromadb.Client()
    ts = int(time.time() * 1000)

    ai_docs = [f"Q: {item['question']}\nA: {item['answer']}" for item in ai_data[:5000]]
    collection = chroma_client.create_collection(
        name=f"ai_{ts}",
        metadata={"hnsw:space": "cosine"}
    )
    for i in range(0, len(ai_docs), 500):
        batch = ai_docs[i:i+500]
        collection.add(documents=batch, ids=[f"ai_{j}" for j in range(i, i+len(batch))])

    # Generate responses for all conditions
    print("\nGenerating responses...")

    results = {
        'constraining_baseline': {'responses': [], 'rouge_l': [], 'bertscore': []},
        'constraining_rag': {'responses': [], 'rouge_l': [], 'bertscore': []},
        'permissive_baseline': {'responses': [], 'rouge_l': [], 'bertscore': []},
        'permissive_rag': {'responses': [], 'rouge_l': [], 'bertscore': []},
    }

    references = []

    for i, item in enumerate(test_data):
        question = item['question']
        reference = item['reference']
        references.append(reference)

        print(f"\n--- Question {i+1}/{num_questions} ---")
        print(f"Q: {question[:70]}...")

        # Get RAG context
        ctx_docs = collection.query(query_texts=[question], n_results=3)['documents'][0]
        context = "\n".join(ctx_docs)

        # Generate all 4 response types
        for condition in results.keys():
            prompt_style = "permissive" if "permissive" in condition else "constraining"
            ctx = context if "rag" in condition else None

            resp = generate_response(question, ctx, prompt_style)
            results[condition]['responses'].append(resp)

            # Compute ROUGE-L immediately
            rouge = compute_rouge_l(reference, resp)
            results[condition]['rouge_l'].append(rouge)

        # Print ROUGE-L scores for this question
        print(f"  ROUGE-L scores:")
        print(f"    Constraining Baseline: {results['constraining_baseline']['rouge_l'][-1]:.3f}")
        print(f"    Constraining RAG:      {results['constraining_rag']['rouge_l'][-1]:.3f}")
        print(f"    Permissive Baseline:   {results['permissive_baseline']['rouge_l'][-1]:.3f}")
        print(f"    Permissive RAG:        {results['permissive_rag']['rouge_l'][-1]:.3f}")

    # Compute BERTScore for all responses (batch processing)
    print("\n" + "=" * 70)
    print("Computing BERTScore (this may take a minute)...")
    print("=" * 70)

    for condition in results.keys():
        print(f"  Computing BERTScore for {condition}...")
        bert_scores = compute_bertscore(references, results[condition]['responses'])
        results[condition]['bertscore'] = bert_scores

    # =============================================================================
    # ANALYSIS
    # =============================================================================

    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)

    # Summary statistics
    summary = {}
    for condition in results.keys():
        summary[condition] = {
            'rouge_l_mean': np.mean(results[condition]['rouge_l']),
            'rouge_l_std': np.std(results[condition]['rouge_l']),
            'bertscore_mean': np.mean(results[condition]['bertscore']),
            'bertscore_std': np.std(results[condition]['bertscore']),
        }

    # Print comparison table
    print("\n┌─────────────────────────┬────────────────────┬────────────────────┐")
    print("│ Condition               │ ROUGE-L            │ BERTScore          │")
    print("├─────────────────────────┼────────────────────┼────────────────────┤")

    for condition in ['constraining_baseline', 'constraining_rag', 'permissive_baseline', 'permissive_rag']:
        s = summary[condition]
        name = condition.replace('_', ' ').title()
        print(f"│ {name:23s} │ {s['rouge_l_mean']:.4f} ± {s['rouge_l_std']:.4f}  │ {s['bertscore_mean']:.4f} ± {s['bertscore_std']:.4f}  │")

    print("└─────────────────────────┴────────────────────┴────────────────────┘")

    # Calculate metric-specific rankings
    print("\n--- RANKINGS BY METRIC ---")

    print("\nROUGE-L Rankings (textual similarity):")
    rouge_rankings = sorted(summary.items(), key=lambda x: x[1]['rouge_l_mean'], reverse=True)
    for rank, (cond, stats) in enumerate(rouge_rankings, 1):
        print(f"  {rank}. {cond.replace('_', ' ').title()}: {stats['rouge_l_mean']:.4f}")

    print("\nBERTScore Rankings (semantic similarity):")
    bert_rankings = sorted(summary.items(), key=lambda x: x[1]['bertscore_mean'], reverse=True)
    for rank, (cond, stats) in enumerate(bert_rankings, 1):
        print(f"  {rank}. {cond.replace('_', ' ').title()}: {stats['bertscore_mean']:.4f}")

    # Calculate the "permissive penalty" for each metric
    print("\n--- METRIC BIAS ANALYSIS ---")

    # Compare constraining vs permissive for each metric
    constr_rag_rouge = summary['constraining_rag']['rouge_l_mean']
    perm_rag_rouge = summary['permissive_rag']['rouge_l_mean']
    rouge_penalty = (perm_rag_rouge - constr_rag_rouge) / constr_rag_rouge * 100

    constr_rag_bert = summary['constraining_rag']['bertscore_mean']
    perm_rag_bert = summary['permissive_rag']['bertscore_mean']
    bert_penalty = (perm_rag_bert - constr_rag_bert) / constr_rag_bert * 100

    print(f"\nPermissive vs Constraining (RAG condition):")
    print(f"  ROUGE-L penalty for permissive: {rouge_penalty:+.1f}%")
    print(f"  BERTScore penalty for permissive: {bert_penalty:+.1f}%")

    # Key finding
    print("\n" + "=" * 70)
    print("KEY FINDING")
    print("=" * 70)

    if abs(bert_penalty) < abs(rouge_penalty):
        print(f"""
✅ HYPOTHESIS CONFIRMED: BERTScore penalizes permissive prompts LESS than ROUGE-L

   ROUGE-L penalty:   {rouge_penalty:+.1f}%
   BERTScore penalty: {bert_penalty:+.1f}%

   Difference: {abs(rouge_penalty) - abs(bert_penalty):.1f} percentage points

   This confirms that ROUGE-L's textual similarity measure unfairly
   penalizes varied, natural responses compared to BERTScore's
   semantic similarity measure.
""")
    else:
        print(f"""
❌ HYPOTHESIS NOT CONFIRMED: BERTScore penalizes permissive prompts MORE

   ROUGE-L penalty:   {rouge_penalty:+.1f}%
   BERTScore penalty: {bert_penalty:+.1f}%

   The results suggest both metrics similarly penalize varied responses,
   or there may be other factors at play.
""")

    # RAG benefit analysis
    print("\n--- RAG BENEFIT BY METRIC ---")

    for metric in ['rouge_l', 'bertscore']:
        print(f"\n{metric.upper()}:")
        for prompt_type in ['constraining', 'permissive']:
            baseline = summary[f'{prompt_type}_baseline'][f'{metric}_mean']
            rag = summary[f'{prompt_type}_rag'][f'{metric}_mean']
            diff = (rag - baseline) / baseline * 100
            print(f"  {prompt_type.title()}: RAG vs Baseline = {diff:+.1f}%")

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'num_questions': num_questions,
        'summary': summary,
        'raw_results': {k: {
            'rouge_l': v['rouge_l'],
            'bertscore': v['bertscore']
        } for k, v in results.items()},
        'analysis': {
            'rouge_penalty_for_permissive': rouge_penalty,
            'bertscore_penalty_for_permissive': bert_penalty,
            'hypothesis_confirmed': abs(bert_penalty) < abs(rouge_penalty)
        }
    }

    output_path = config.RESULTS_DIR / "bertscore_comparison_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")

    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BERTScore vs ROUGE-L Comparison")
    parser.add_argument('--questions', type=int, default=5, help='Number of test questions')
    args = parser.parse_args()

    results = run_bertscore_experiment(num_questions=args.questions)
