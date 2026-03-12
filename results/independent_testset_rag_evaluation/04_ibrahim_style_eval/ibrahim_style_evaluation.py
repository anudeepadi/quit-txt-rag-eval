#!/usr/bin/env python3
"""
Ibrahim-Style RAG Evaluation

This script implements the fixes identified by Ralph Wiggum cross-validation:
1. PERMISSIVE prompt design (not constraining)
2. HYBRID retrieval (keyword + vector scoring)
3. Detailed system prompts with guidelines

Author: Research Team
Date: January 2026
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings("ignore")

import numpy as np
from openai import OpenAI
import chromadb
from rouge_score import rouge_scorer

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
    MAX_TOKENS = 300  # Increased for more detailed responses
    NUM_RETRIEVAL_DOCS = 3
    RESULTS_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent.parent.parent / "data"

config = Config()

# =============================================================================
# IBRAHIM-STYLE PROMPTS (PERMISSIVE, NOT CONSTRAINING)
# =============================================================================

IBRAHIM_SYSTEM_PROMPT = """You are a compassionate smoking cessation counselor working with the QuitTxt program. You provide personalized, evidence-based support to help people quit smoking.

RESPONSE GUIDELINES:
1. **Use Protocol Strategies**: Draw from the evidence-based strategies in the context below, but express them naturally
2. **Be Conversational**: Don't copy-paste protocol language; explain strategies in your own words adapted to the user's specific situation
3. **Provide Specifics**: When techniques are mentioned (4 Ds, breathing exercises, etc.), explain HOW to use them, not just THAT they exist
4. **Vary Your Responses**: Avoid repeating the same phrases or metaphors; use different examples and language each time
5. **Personalize**: Reference the user's specific situation, emotions, or previous messages when relevant
6. **Be Empathetic First**: Acknowledge feelings before jumping to strategies
7. **Length**: Keep responses substantive (3-5 sentences) but not overwhelming

AVOID:
- Copying exact protocol phrases verbatim
- Repeating the same metaphors or examples
- Just listing information without explanation
- Generic advice that ignores the provided context
"""

CONTEXT_INSTRUCTIONS = """
HOW TO USE THE CONTEXT:
- Understand the PRINCIPLES and STRATEGIES from the information above
- Express these strategies in natural, conversational language tailored to this user
- Combine the context with your own knowledge for the best response
- Use your own words while staying true to the evidence-based approaches
- You may supplement with your own knowledge when appropriate
"""

# Original constraining prompt for comparison
ORIGINAL_SYSTEM_PROMPT = """You are a compassionate smoking cessation counselor. Use the provided context to answer. Be concise (2-4 sentences)."""


# =============================================================================
# HYBRID RETRIEVAL (KEYWORD + VECTOR)
# =============================================================================

# Keyword map for topic-based scoring (from CLAUDE.md)
KEYWORD_MAP = {
    'craving': ['craving', 'urge', 'want', 'desire', 'temptation', 'trigger'],
    'motivation': ['motivation', 'reason', 'why', 'benefit', 'goal', 'purpose'],
    'support': ['support', 'help', 'friend', 'family', 'group', 'buddy'],
    'relapse': ['relapse', 'slip', 'smoke again', 'failed', 'setback', 'restart'],
    'withdrawal': ['withdrawal', 'symptom', 'irritable', 'anxious', 'headache', 'tired'],
    'stress': ['stress', 'anxious', 'worried', 'overwhelmed', 'pressure', 'nervous'],
    'health': ['health', 'lung', 'heart', 'cancer', 'breathe', 'cough', 'doctor'],
    'trigger': ['trigger', 'situation', 'habit', 'routine', 'coffee', 'alcohol', 'after meal'],
    'strategy': ['strategy', 'technique', 'method', 'tip', 'how to', 'way to'],
    'progress': ['progress', 'day', 'week', 'milestone', 'achievement', 'success'],
}


def compute_keyword_score(query: str, document: str) -> float:
    """Compute keyword-based relevance score (Ibrahim's approach)."""
    query_lower = query.lower()
    doc_lower = document.lower()
    score = 0.0

    # Direct keyword matching (+2 pts per match)
    query_words = set(re.findall(r'\w+', query_lower))
    doc_words = set(re.findall(r'\w+', doc_lower))
    common_words = query_words & doc_words
    score += len(common_words) * 0.5  # Scaled down

    # Topic matching (+1 pt per topic)
    for topic, keywords in KEYWORD_MAP.items():
        query_has_topic = any(kw in query_lower for kw in keywords)
        doc_has_topic = any(kw in doc_lower for kw in keywords)
        if query_has_topic and doc_has_topic:
            score += 1.0

    # Title/header matching (+3 pts)
    # Check if query terms appear in first line (likely title)
    first_line = doc_lower.split('\n')[0] if '\n' in doc_lower else doc_lower[:100]
    title_matches = sum(1 for word in query_words if word in first_line and len(word) > 3)
    score += title_matches * 0.5

    return score


def hybrid_retrieve(
    collection: chromadb.Collection,
    query: str,
    documents: List[str],
    n_results: int = 3,
    keyword_weight: float = 0.3
) -> Tuple[List[str], List[float]]:
    """Hybrid retrieval combining vector similarity and keyword scoring."""

    # Get vector similarity results
    results = collection.query(query_texts=[query], n_results=min(n_results * 3, len(documents)))

    if not results['documents'] or not results['documents'][0]:
        return [], []

    vector_docs = results['documents'][0]
    vector_distances = results['distances'][0]

    # Combine with keyword scores
    scored_results = []
    for doc, dist in zip(vector_docs, vector_distances):
        # Convert distance to similarity (lower distance = higher similarity)
        vector_score = 1 - dist  # Cosine distance to similarity
        keyword_score = compute_keyword_score(query, doc)

        # Normalize keyword score (rough normalization)
        keyword_score_norm = min(keyword_score / 5.0, 1.0)

        # Combined score
        combined_score = (1 - keyword_weight) * vector_score + keyword_weight * keyword_score_norm
        scored_results.append((doc, combined_score, dist))

    # Sort by combined score (descending)
    scored_results.sort(key=lambda x: x[1], reverse=True)

    # Return top n
    top_results = scored_results[:n_results]
    return [r[0] for r in top_results], [r[2] for r in top_results]


# =============================================================================
# RESPONSE GENERATION
# =============================================================================

def generate_response_ibrahim_style(question: str, context: Optional[str] = None) -> str:
    """Generate response using Ibrahim's permissive prompt style."""
    try:
        if context:
            messages = [
                {"role": "system", "content": IBRAHIM_SYSTEM_PROMPT},
                {"role": "user", "content": f"""=== RELEVANT CONTEXT ===
{context}

{CONTEXT_INSTRUCTIONS}

=== USER QUESTION ===
{question}

Please provide a helpful, personalized response drawing from the context above while using natural, conversational language."""}
            ]
        else:
            messages = [
                {"role": "system", "content": IBRAHIM_SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ]

        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def generate_response_original_style(question: str, context: Optional[str] = None) -> str:
    """Generate response using original constraining prompt style."""
    try:
        if context:
            messages = [
                {"role": "system", "content": ORIGINAL_SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]
        else:
            messages = [
                {"role": "system", "content": "You are a compassionate smoking cessation counselor. Answer concisely (2-4 sentences)."},
                {"role": "user", "content": question}
            ]

        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            temperature=config.TEMPERATURE,
            max_tokens=200,  # Original limit
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# EVALUATION
# =============================================================================

def compute_rouge_l(reference: str, candidate: str) -> float:
    """Compute ROUGE-L F1 score."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores['rougeL'].fmeasure


def load_test_data() -> List[Dict]:
    """Load the independent test set."""
    test_file = config.RESULTS_DIR / "FINAL_independent_test_set.json"
    with open(test_file) as f:
        data = json.load(f)
    return data['test_data']


def load_datasets() -> Tuple[List[Dict], List[Dict]]:
    """Load human-curated and AI-generated datasets."""
    human_path = config.DATA_DIR / "qa.jsonl"
    ai_path = config.DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl"

    human_data = []
    if human_path.exists():
        with open(human_path) as f:
            for line in f:
                if line.strip():
                    human_data.append(json.loads(line))

    ai_data = []
    if ai_path.exists():
        with open(ai_path) as f:
            for line in f:
                if line.strip():
                    ai_data.append(json.loads(line))

    return human_data, ai_data


def run_comparison_experiment(num_questions: int = 5) -> Dict:
    """Run comparison between original and Ibrahim-style approaches."""

    print("=" * 60)
    print("IBRAHIM-STYLE vs ORIGINAL APPROACH COMPARISON")
    print("=" * 60)

    # Load data
    test_data = load_test_data()[:num_questions]
    human_data, ai_data = load_datasets()

    print(f"Testing with {len(test_data)} questions")
    print(f"Human QA pairs: {len(human_data)}")
    print(f"AI QA pairs: {len(ai_data)}")

    # Create collections
    print("\nCreating ChromaDB collections...")
    chroma_client = chromadb.Client()
    ts = int(time.time() * 1000)

    # AI-generated collection
    ai_docs = [f"Q: {item['question']}\nA: {item['answer']}" for item in ai_data[:5000]]
    ai_collection = chroma_client.create_collection(
        name=f"ai_{ts}",
        metadata={"hnsw:space": "cosine"}
    )
    for i in range(0, len(ai_docs), 500):
        batch = ai_docs[i:i+500]
        ai_collection.add(documents=batch, ids=[f"ai_{j}" for j in range(i, i+len(batch))])

    # Human-curated collection
    human_docs = [f"Q: {item['question']}\nA: {item['answer']}" for item in human_data]
    human_collection = chroma_client.create_collection(
        name=f"human_{ts}",
        metadata={"hnsw:space": "cosine"}
    )
    for i in range(0, len(human_docs), 500):
        batch = human_docs[i:i+500]
        human_collection.add(documents=batch, ids=[f"human_{j}" for j in range(i, i+len(batch))])

    # Run evaluations
    results = {
        'original_baseline': [],
        'original_rag': [],
        'ibrahim_baseline': [],
        'ibrahim_rag_vector': [],
        'ibrahim_rag_hybrid': [],
    }

    print("\nGenerating responses...")
    for i, item in enumerate(test_data):
        question = item['question']
        reference = item['reference']

        print(f"\n--- Question {i+1}/{len(test_data)} ---")
        print(f"Q: {question[:80]}...")

        # === ORIGINAL APPROACH ===

        # Original baseline
        resp = generate_response_original_style(question, None)
        score = compute_rouge_l(reference, resp)
        results['original_baseline'].append(score)
        print(f"  Original Baseline: {score:.3f}")

        # Original RAG (vector only)
        ctx_docs = ai_collection.query(query_texts=[question], n_results=3)['documents'][0]
        ctx = "\n".join(ctx_docs)
        resp = generate_response_original_style(question, ctx)
        score = compute_rouge_l(reference, resp)
        results['original_rag'].append(score)
        print(f"  Original RAG: {score:.3f}")

        # === IBRAHIM APPROACH ===

        # Ibrahim baseline
        resp = generate_response_ibrahim_style(question, None)
        score = compute_rouge_l(reference, resp)
        results['ibrahim_baseline'].append(score)
        print(f"  Ibrahim Baseline: {score:.3f}")

        # Ibrahim RAG (vector only)
        resp = generate_response_ibrahim_style(question, ctx)
        score = compute_rouge_l(reference, resp)
        results['ibrahim_rag_vector'].append(score)
        print(f"  Ibrahim RAG (vector): {score:.3f}")

        # Ibrahim RAG (hybrid retrieval)
        hybrid_docs, hybrid_dists = hybrid_retrieve(ai_collection, question, ai_docs, n_results=3)
        ctx_hybrid = "\n".join(hybrid_docs)
        resp = generate_response_ibrahim_style(question, ctx_hybrid)
        score = compute_rouge_l(reference, resp)
        results['ibrahim_rag_hybrid'].append(score)
        print(f"  Ibrahim RAG (hybrid): {score:.3f}")

    # Compute summary statistics
    summary = {}
    for approach, scores in results.items():
        summary[approach] = {
            'mean': np.mean(scores),
            'std': np.std(scores),
            'scores': scores
        }

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY (ROUGE-L)")
    print("=" * 60)

    print("\n--- ORIGINAL APPROACH ---")
    print(f"  Baseline:        {summary['original_baseline']['mean']:.4f} ± {summary['original_baseline']['std']:.4f}")
    print(f"  RAG (vector):    {summary['original_rag']['mean']:.4f} ± {summary['original_rag']['std']:.4f}")

    orig_diff = (summary['original_rag']['mean'] - summary['original_baseline']['mean']) / summary['original_baseline']['mean'] * 100
    print(f"  RAG vs Baseline: {orig_diff:+.1f}%")

    print("\n--- IBRAHIM APPROACH ---")
    print(f"  Baseline:        {summary['ibrahim_baseline']['mean']:.4f} ± {summary['ibrahim_baseline']['std']:.4f}")
    print(f"  RAG (vector):    {summary['ibrahim_rag_vector']['mean']:.4f} ± {summary['ibrahim_rag_vector']['std']:.4f}")
    print(f"  RAG (hybrid):    {summary['ibrahim_rag_hybrid']['mean']:.4f} ± {summary['ibrahim_rag_hybrid']['std']:.4f}")

    ibr_vec_diff = (summary['ibrahim_rag_vector']['mean'] - summary['ibrahim_baseline']['mean']) / summary['ibrahim_baseline']['mean'] * 100
    ibr_hyb_diff = (summary['ibrahim_rag_hybrid']['mean'] - summary['ibrahim_baseline']['mean']) / summary['ibrahim_baseline']['mean'] * 100
    print(f"  RAG (vector) vs Baseline: {ibr_vec_diff:+.1f}%")
    print(f"  RAG (hybrid) vs Baseline: {ibr_hyb_diff:+.1f}%")

    print("\n--- COMPARISON ---")
    prompt_effect = (summary['ibrahim_baseline']['mean'] - summary['original_baseline']['mean']) / summary['original_baseline']['mean'] * 100
    retrieval_effect = (summary['ibrahim_rag_hybrid']['mean'] - summary['ibrahim_rag_vector']['mean']) / summary['ibrahim_rag_vector']['mean'] * 100
    total_effect = (summary['ibrahim_rag_hybrid']['mean'] - summary['original_rag']['mean']) / summary['original_rag']['mean'] * 100

    print(f"  Prompt effect (Ibrahim vs Original baseline): {prompt_effect:+.1f}%")
    print(f"  Retrieval effect (hybrid vs vector): {retrieval_effect:+.1f}%")
    print(f"  Total improvement (Ibrahim hybrid vs Original RAG): {total_effect:+.1f}%")

    # Determine winner
    print("\n--- WINNERS ---")
    approaches = [
        ('Original Baseline', summary['original_baseline']['mean']),
        ('Original RAG', summary['original_rag']['mean']),
        ('Ibrahim Baseline', summary['ibrahim_baseline']['mean']),
        ('Ibrahim RAG (vector)', summary['ibrahim_rag_vector']['mean']),
        ('Ibrahim RAG (hybrid)', summary['ibrahim_rag_hybrid']['mean']),
    ]
    approaches.sort(key=lambda x: x[1], reverse=True)

    for rank, (name, score) in enumerate(approaches, 1):
        print(f"  {rank}. {name}: {score:.4f}")

    return {
        'summary': summary,
        'test_questions': len(test_data),
        'timestamp': datetime.now().isoformat(),
        'winner': approaches[0][0],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ibrahim-Style RAG Evaluation")
    parser.add_argument('--questions', type=int, default=5, help='Number of test questions')
    args = parser.parse_args()

    results = run_comparison_experiment(num_questions=args.questions)

    # Save results
    output_path = config.RESULTS_DIR / "ibrahim_style_comparison.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")
