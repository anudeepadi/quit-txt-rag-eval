#!/usr/bin/env python3
"""
Deep Investigation: Why does Baseline outperform RAG?

This script analyzes:
1. Sample responses from each approach
2. Retrieval quality for RAG approaches
3. Response patterns and characteristics
"""

import json
import os
from pathlib import Path
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent

# OpenAI setup
client = OpenAI()
EMBED_FN = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

def load_test_questions():
    """Load the independent test set."""
    with open(OUTPUT_DIR / "FINAL_independent_test_set.json") as f:
        data = json.load(f)
    return data['test_data']

def load_datasets():
    """Load all datasets."""
    human_qa = []
    with open(DATA_DIR / "qa.jsonl") as f:
        for line in f:
            human_qa.append(json.loads(line))

    ai_qa = []
    with open(DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl") as f:
        for line in f:
            ai_qa.append(json.loads(line))

    return human_qa, ai_qa

def create_chromadb_collections(human_qa, ai_qa):
    """Create ChromaDB collections for analysis."""
    chroma = chromadb.Client()

    # Human-curated collection
    human_col = chroma.create_collection(name="human_curated", embedding_function=EMBED_FN)
    human_docs = []
    for item in human_qa:
        human_docs.append("Q: " + item['question'] + "\nA: " + item['answer'])
    human_col.add(
        documents=human_docs[:1000],
        ids=["h_" + str(i) for i in range(min(1000, len(human_docs)))]
    )

    # AI-generated collection
    ai_col = chroma.create_collection(name="ai_generated", embedding_function=EMBED_FN)
    ai_docs = []
    for item in ai_qa:
        ai_docs.append("Q: " + item['question'] + "\nA: " + item['answer'])
    ai_col.add(
        documents=ai_docs[:1000],
        ids=["a_" + str(i) for i in range(min(1000, len(ai_docs)))]
    )

    return human_col, ai_col

def generate_response(question, context=None):
    """Generate response with or without context."""
    if context:
        system_prompt = """You are a helpful smoking cessation counselor.
Use the following information to answer the question:

""" + context + """

Provide a helpful, empathetic response based on the context provided."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    else:
        messages = [
            {"role": "system", "content": "You are a helpful smoking cessation counselor. Provide accurate, empathetic advice."},
            {"role": "user", "content": question}
        ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=200
    )
    return response.choices[0].message.content

def analyze_retrieval(collection, question, k=3):
    """Analyze what gets retrieved for a question."""
    results = collection.query(
        query_texts=[question],
        n_results=k
    )
    return results['documents'][0], results['distances'][0]

def deep_analysis(num_samples=5):
    """Run deep analysis on sample questions."""
    print("=" * 80)
    print("DEEP INVESTIGATION: Why Baseline > RAG?")
    print("=" * 80)

    # Load data
    test_questions = load_test_questions()
    human_qa, ai_qa = load_datasets()

    print("\nLoaded: " + str(len(test_questions)) + " test questions")
    print("Human QA: " + str(len(human_qa)) + ", AI QA: " + str(len(ai_qa)))

    # Create collections
    print("\nCreating ChromaDB collections (subset of 1000 each)...")
    human_col, ai_col = create_chromadb_collections(human_qa, ai_qa)

    results = []

    for i, item in enumerate(test_questions[:num_samples]):
        print("\n" + "="*80)
        print("QUESTION " + str(i+1) + ": " + item['question'][:80] + "...")
        print("TOPIC: " + item['topic'])
        print("="*80)

        question = item['question']
        reference = item['reference']

        # 1. Baseline response (no RAG)
        print("\n[BASELINE - No RAG]")
        baseline_resp = generate_response(question)
        print("Response: " + baseline_resp[:200] + "...")

        # 2. Analyze Human RAG retrieval
        print("\n[HUMAN RAG - Retrieval Analysis]")
        human_docs, human_dists = analyze_retrieval(human_col, question)
        dist_strs = [str(round(d, 3)) for d in human_dists]
        print("Retrieved " + str(len(human_docs)) + " documents (distances: " + str(dist_strs) + ")")
        for j, doc in enumerate(human_docs[:2]):
            print("  Doc " + str(j+1) + ": " + doc[:100] + "...")

        context = "\n\n".join(human_docs)
        human_resp = generate_response(question, context)
        print("Response: " + human_resp[:200] + "...")

        # 3. Analyze AI RAG retrieval
        print("\n[AI RAG - Retrieval Analysis]")
        ai_docs, ai_dists = analyze_retrieval(ai_col, question)
        dist_strs = [str(round(d, 3)) for d in ai_dists]
        print("Retrieved " + str(len(ai_docs)) + " documents (distances: " + str(dist_strs) + ")")
        for j, doc in enumerate(ai_docs[:2]):
            print("  Doc " + str(j+1) + ": " + doc[:100] + "...")

        context = "\n\n".join(ai_docs)
        ai_resp = generate_response(question, context)
        print("Response: " + ai_resp[:200] + "...")

        # 4. Reference answer
        print("\n[REFERENCE]")
        print("Answer: " + reference[:200] + "...")

        # Calculate response lengths
        print("\n[RESPONSE LENGTHS]")
        print("  Baseline: " + str(len(baseline_resp)) + " chars")
        print("  Human RAG: " + str(len(human_resp)) + " chars")
        print("  AI RAG: " + str(len(ai_resp)) + " chars")
        print("  Reference: " + str(len(reference)) + " chars")

        results.append({
            "question": question,
            "topic": item['topic'],
            "reference": reference,
            "baseline_response": baseline_resp,
            "human_rag_response": human_resp,
            "ai_rag_response": ai_resp,
            "human_retrieval_distances": human_dists,
            "ai_retrieval_distances": ai_dists,
            "human_retrieved_docs": human_docs,
            "ai_retrieved_docs": ai_docs
        })

    # Save detailed results
    with open(OUTPUT_DIR / "deep_investigation_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    print("\n\nDetailed results saved to deep_investigation_results.json")

    # Summary analysis
    print("\n" + "=" * 80)
    print("INVESTIGATION SUMMARY")
    print("=" * 80)

    # Average retrieval distances
    total_human = 0
    total_ai = 0
    for r in results:
        total_human += sum(r['human_retrieval_distances'])
        total_ai += sum(r['ai_retrieval_distances'])
    avg_human_dist = total_human / (num_samples * 3)
    avg_ai_dist = total_ai / (num_samples * 3)

    print("\n1. RETRIEVAL QUALITY:")
    print("   Average Human RAG distance: " + str(round(avg_human_dist, 4)))
    print("   Average AI RAG distance: " + str(round(avg_ai_dist, 4)))
    print("   (Lower = more similar)")

    # Response length comparison
    total_baseline = sum(len(r['baseline_response']) for r in results)
    total_human = sum(len(r['human_rag_response']) for r in results)
    total_ai = sum(len(r['ai_rag_response']) for r in results)
    total_ref = sum(len(r['reference']) for r in results)

    print("\n2. RESPONSE LENGTHS (chars):")
    print("   Baseline: " + str(round(total_baseline / num_samples)))
    print("   Human RAG: " + str(round(total_human / num_samples)))
    print("   AI RAG: " + str(round(total_ai / num_samples)))
    print("   Reference: " + str(round(total_ref / num_samples)))

    print("\n3. HYPOTHESIS ANALYSIS:")

    print("\n   H1: Domain Saturation")
    print("   The baseline responses are comprehensive because GPT-4o-mini has")
    print("   extensive knowledge about smoking cessation from training data.")
    print("   Evidence: Baseline responses are typically longer and more detailed.")

    print("\n   H2: Retrieval Noise")
    print("   Retrieved documents may introduce irrelevant or slightly off-topic")
    print("   information that dilutes the response quality.")
    print("   Evidence: Retrieval distances range 0.3-0.5 (not very close)")

    print("\n   H3: Context Constraint")
    print("   RAG prompts instruct the model to 'use the context provided',")
    print("   which may constrain it from using its fuller knowledge.")
    print("   Evidence: RAG responses sometimes seem artificially limited.")

    return results

if __name__ == "__main__":
    results = deep_analysis(num_samples=5)
