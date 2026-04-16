#!/usr/bin/env python3
"""
Sensitivity Analysis: Embedding Model & LLM Dependency
Tests whether "Baseline > RAG" finding holds with:
1. Better embeddings (OpenAI text-embedding-3-small)
2. Weaker LLM (GPT-3.5-turbo)

Author: Research Team
Date: January 2026
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

# Load environment
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))

from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from rouge_score import rouge_scorer

# Configuration
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RESULTS_DIR = Path(__file__).parent

# Test configurations
CONFIGS = [
    {"name": "Original", "embedding": "default", "model": "gpt-4o-mini"},
    {"name": "OpenAI-Embed", "embedding": "openai", "model": "gpt-4o-mini"},
    {"name": "Weaker-LLM", "embedding": "default", "model": "gpt-3.5-turbo"},
    {"name": "OpenAI-Embed+Weaker", "embedding": "openai", "model": "gpt-3.5-turbo"},
]

def load_test_questions(n: int = 5) -> List[Dict]:
    """Load subset of test questions."""
    with open(RESULTS_DIR / "FINAL_independent_test_set.json") as f:
        data = json.load(f)
    return data['test_data'][:n]

def load_knowledge_base() -> List[str]:
    """Load AI-generated knowledge base."""
    docs = []
    ai_path = DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl"
    with open(ai_path) as f:
        for i, line in enumerate(f):
            if i >= 1000:  # Limit for speed
                break
            d = json.loads(line)
            docs.append(f"Q: {d['question']}\nA: {d['answer']}")
    return docs

def create_collection_with_embeddings(docs: List[str], use_openai: bool = False):
    """Create ChromaDB collection with specified embeddings."""
    chroma_client = chromadb.Client()
    ts = int(time.time() * 1000)

    if use_openai:
        # Use OpenAI embeddings
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        collection = chroma_client.create_collection(
            name=f"test_{ts}",
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"}
        )
    else:
        # Use default embeddings (all-MiniLM-L6-v2)
        collection = chroma_client.create_collection(
            name=f"test_{ts}",
            metadata={"hnsw:space": "cosine"}
        )

    # Add documents in batches
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        collection.add(
            documents=batch,
            ids=[f"doc_{j}" for j in range(i, i+len(batch))]
        )

    return collection

def generate_response(question: str, context: Optional[str], model: str) -> str:
    """Generate response with specified model."""
    if context:
        messages = [
            {"role": "system", "content": "You are a smoking cessation counselor. Use the context to answer concisely."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    else:
        messages = [
            {"role": "system", "content": "You are a smoking cessation counselor. Answer concisely."},
            {"role": "user", "content": question}
        ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def run_sensitivity_analysis():
    """Run full sensitivity analysis."""
    print("=" * 60)
    print("SENSITIVITY ANALYSIS: Embedding & Model Dependency")
    print("=" * 60)
    print()

    # Load data
    print("Loading data...")
    test_questions = load_test_questions(5)  # Use 5 questions
    knowledge_base = load_knowledge_base()
    print(f"  Test questions: {len(test_questions)}")
    print(f"  Knowledge base: {len(knowledge_base)} docs")
    print()

    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    results = {}

    for config in CONFIGS:
        print(f"\n{'='*60}")
        print(f"Testing: {config['name']}")
        print(f"  Embedding: {config['embedding']}")
        print(f"  Model: {config['model']}")
        print("=" * 60)

        # Create collection with appropriate embeddings
        use_openai_embed = config['embedding'] == 'openai'
        print(f"Creating collection with {'OpenAI' if use_openai_embed else 'default'} embeddings...")
        collection = create_collection_with_embeddings(knowledge_base, use_openai_embed)

        baseline_scores = []
        rag_scores = []
        retrieval_distances = []

        for i, q in enumerate(test_questions):
            print(f"  Q{i+1}: {q['question'][:50]}...")

            # Baseline (no RAG)
            baseline_answer = generate_response(q['question'], None, config['model'])
            baseline_score = scorer.score(q['reference'], baseline_answer)['rougeL'].fmeasure
            baseline_scores.append(baseline_score)

            # RAG
            results_q = collection.query(query_texts=[q['question']], n_results=3)
            context = "\n\n".join(results_q['documents'][0])
            avg_distance = np.mean(results_q['distances'][0]) if results_q['distances'][0] else 0
            retrieval_distances.append(avg_distance)

            rag_answer = generate_response(q['question'], context, config['model'])
            rag_score = scorer.score(q['reference'], rag_answer)['rougeL'].fmeasure
            rag_scores.append(rag_score)

            print(f"      Baseline: {baseline_score:.3f}, RAG: {rag_score:.3f}, Dist: {avg_distance:.3f}")

        # Store results
        results[config['name']] = {
            'config': config,
            'baseline_mean': np.mean(baseline_scores),
            'rag_mean': np.mean(rag_scores),
            'baseline_scores': baseline_scores,
            'rag_scores': rag_scores,
            'avg_retrieval_distance': np.mean(retrieval_distances),
            'winner': 'Baseline' if np.mean(baseline_scores) > np.mean(rag_scores) else 'RAG'
        }

        print(f"\n  Results for {config['name']}:")
        print(f"    Baseline Mean: {np.mean(baseline_scores):.4f}")
        print(f"    RAG Mean: {np.mean(rag_scores):.4f}")
        print(f"    Avg Retrieval Distance: {np.mean(retrieval_distances):.4f}")
        print(f"    Winner: {results[config['name']]['winner']}")

    # Summary
    print("\n" + "=" * 60)
    print("SENSITIVITY ANALYSIS SUMMARY")
    print("=" * 60)
    print()
    print(f"{'Config':<25} {'Baseline':<10} {'RAG':<10} {'Retr.Dist':<10} {'Winner':<10}")
    print("-" * 65)
    for name, r in results.items():
        print(f"{name:<25} {r['baseline_mean']:.4f}     {r['rag_mean']:.4f}     {r['avg_retrieval_distance']:.4f}     {r['winner']}")

    print()

    # Key findings
    baseline_wins = sum(1 for r in results.values() if r['winner'] == 'Baseline')
    rag_wins = len(results) - baseline_wins

    print("KEY FINDINGS:")
    print(f"  Baseline wins: {baseline_wins}/{len(results)} configurations")
    print(f"  RAG wins: {rag_wins}/{len(results)} configurations")
    print()

    if baseline_wins == len(results):
        print("  ✅ Finding ROBUST: Baseline > RAG across all configurations")
    elif rag_wins == len(results):
        print("  ❌ Finding NOT ROBUST: RAG > Baseline with better config")
    else:
        print("  ⚠️ Finding PARTIALLY DEPENDENT on configuration")
        for name, r in results.items():
            if r['winner'] == 'RAG':
                print(f"     → RAG wins with: {name}")

    # Save results
    output_path = RESULTS_DIR / "sensitivity_analysis_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_path}")

    return results

if __name__ == "__main__":
    run_sensitivity_analysis()
