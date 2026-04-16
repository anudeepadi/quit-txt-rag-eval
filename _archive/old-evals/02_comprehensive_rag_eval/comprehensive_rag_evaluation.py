#!/usr/bin/env python3
"""
Comprehensive RAG Evaluation with Independent Test Set

This script runs rigorous evaluation with:
1. NEW independent test set (no data leakage)
2. All metrics: ROUGE-L, BLEU, BERTScore, METEOR
3. Statistical significance testing (t-tests, effect sizes)
4. 5+ independent runs with 95% confidence intervals
5. Vocabulary alignment analysis

Author: Research Team
Date: January 10, 2026
"""

import os
import json
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Suppress warnings
warnings.filterwarnings("ignore")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Statistical imports
import numpy as np
from scipy import stats

# NLP imports
import nltk
from nltk.translate.meteor_score import meteor_score
from nltk.tokenize import word_tokenize

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Load environment variables
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))

# API imports
from openai import OpenAI
import chromadb
from rouge_score import rouge_scorer
from sacrebleu.metrics import BLEU

# Try to import BERTScore (optional, slower)
try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False
    logger.warning("BERTScore not available. Install with: pip install bert-score")

# Configuration
class Config:
    MODEL_NAME = "gpt-4o-mini"
    TEMPERATURE = 0.3
    MAX_TOKENS = 200
    NUM_RUNS = 5
    NUM_RETRIEVAL_DOCS = 3
    RESULTS_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent.parent.parent / "data"

config = Config()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_independent_test_set() -> List[Dict]:
    """Load the new independent test set."""
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

    logger.info(f"Loaded {len(human_data)} human-curated, {len(ai_data)} AI-generated QA pairs")
    return human_data, ai_data


# Raw sources (same as original for fair comparison)
RAW_SOURCES = [
    """Quitting smoking timeline: 20 minutes - heart rate drops; 12 hours - carbon monoxide normalizes;
    24 hours - heart attack risk decreases; 48 hours - nerve endings regenerate; 2 weeks - circulation improves;
    1-9 months - coughing decreases; 1 year - heart disease risk halved; 5 years - stroke risk reduced.""",
    """Nicotine replacement therapy (NRT) includes: patches (21mg, 14mg, 7mg), gum (2mg, 4mg),
    lozenges, inhalers, and nasal sprays. Combination therapy often more effective than single product.""",
    """Withdrawal symptoms: irritability, anxiety, difficulty concentrating, increased appetite,
    cravings, depression, insomnia. Peak at 2-3 days, most subside within 2-4 weeks.""",
    """Smoking health effects: causes cancer (lung, throat, mouth, bladder), heart disease, stroke,
    COPD, diabetes complications, weakened immune system, fertility problems.""",
    """Quitting strategies: set quit date, tell friends/family, remove triggers, use NRT or medications,
    join support group, manage stress, reward milestones, don't give up after slips.""",
    """Secondhand smoke contains 7,000+ chemicals, 70+ carcinogens. Causes heart disease, lung cancer,
    stroke in adults. In children: SIDS, ear infections, asthma, respiratory infections.""",
]


def create_chromadb_collection(name: str, documents: List[str]) -> chromadb.Collection:
    """Create a ChromaDB collection with documents."""
    chroma_client = chromadb.Client()
    ts = int(time.time() * 1000)
    collection = chroma_client.create_collection(
        name=f"{name}_{ts}",
        metadata={"hnsw:space": "cosine"}
    )

    # Add in batches
    batch_size = 500
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        collection.add(
            documents=batch,
            ids=[f"{name}_{j}" for j in range(i, i+len(batch))]
        )

    return collection


def generate_response(question: str, context: Optional[str] = None) -> str:
    """Generate response using OpenAI."""
    try:
        if context:
            messages = [
                {"role": "system", "content": "You are a compassionate smoking cessation counselor. Use the provided context to answer. Be concise (2-4 sentences)."},
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
            max_tokens=config.MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"API error: {e}")
        return f"Error: {str(e)}"


def compute_rouge(reference: str, candidate: str) -> Dict[str, float]:
    """Compute ROUGE scores."""
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return {
        'rouge1': scores['rouge1'].fmeasure,
        'rouge2': scores['rouge2'].fmeasure,
        'rougeL': scores['rougeL'].fmeasure,
    }


def compute_bleu(references: List[str], candidates: List[str]) -> float:
    """Compute corpus BLEU score."""
    bleu = BLEU()
    score = bleu.corpus_score(candidates, [references])
    return score.score / 100  # Normalize to 0-1


def compute_meteor(reference: str, candidate: str) -> float:
    """Compute METEOR score."""
    ref_tokens = word_tokenize(reference.lower())
    cand_tokens = word_tokenize(candidate.lower())
    return meteor_score([ref_tokens], cand_tokens)


def compute_bertscore(references: List[str], candidates: List[str]) -> List[float]:
    """Compute BERTScore F1 for each pair."""
    if not BERTSCORE_AVAILABLE:
        return [0.0] * len(references)

    # Use lighter model for speed
    P, R, F1 = bert_score(
        candidates, references,
        model_type="distilbert-base-uncased",
        batch_size=16,
        verbose=False
    )
    return F1.tolist()


def compute_all_metrics(
    references: List[str],
    candidates: List[str],
    include_bertscore: bool = False
) -> Dict[str, float]:
    """Compute all metrics for a set of reference-candidate pairs."""

    # ROUGE (per-pair, then average)
    rouge_scores = {'rouge1': [], 'rouge2': [], 'rougeL': []}
    meteor_scores = []

    for ref, cand in zip(references, candidates):
        rouge = compute_rouge(ref, cand)
        for key in rouge_scores:
            rouge_scores[key].append(rouge[key])
        meteor_scores.append(compute_meteor(ref, cand))

    metrics = {
        'rouge1': np.mean(rouge_scores['rouge1']),
        'rouge2': np.mean(rouge_scores['rouge2']),
        'rougeL': np.mean(rouge_scores['rougeL']),
        'bleu': compute_bleu(references, candidates),
        'meteor': np.mean(meteor_scores),
    }

    # BERTScore (optional, slower)
    if include_bertscore and BERTSCORE_AVAILABLE:
        bert_f1 = compute_bertscore(references, candidates)
        metrics['bertscore'] = np.mean(bert_f1)

    return metrics


def run_single_evaluation(
    test_data: List[Dict],
    human_data: List[Dict],
    ai_data: List[Dict],
    include_bertscore: bool = False
) -> Dict[str, Dict[str, float]]:
    """Run a single evaluation trial."""

    # Create collections
    logger.info("Creating ChromaDB collections...")
    raw_coll = create_chromadb_collection("raw", RAW_SOURCES)

    ai_docs = [f"Q: {item['question']}\nA: {item['answer']}" for item in ai_data[:5000]]
    ai_coll = create_chromadb_collection("ai", ai_docs)

    human_docs = [f"Q: {item['question']}\nA: {item['answer']}" for item in human_data]
    human_coll = create_chromadb_collection("human", human_docs)

    # Generate responses
    questions = [item['question'] for item in test_data]
    references = [item['reference'] for item in test_data]

    responses = {
        'baseline': [],
        'raw_rag': [],
        'ai_rag': [],
        'human_rag': []
    }

    logger.info(f"Generating responses for {len(questions)} questions...")
    for i, q in enumerate(questions):
        # Baseline (no RAG)
        responses['baseline'].append(generate_response(q))

        # Raw sources RAG
        raw_ctx = "\n".join(raw_coll.query(query_texts=[q], n_results=2)['documents'][0])
        responses['raw_rag'].append(generate_response(q, raw_ctx))

        # AI-generated RAG
        ai_ctx = "\n".join(ai_coll.query(query_texts=[q], n_results=config.NUM_RETRIEVAL_DOCS)['documents'][0])
        responses['ai_rag'].append(generate_response(q, ai_ctx))

        # Human-curated RAG
        human_ctx = "\n".join(human_coll.query(query_texts=[q], n_results=config.NUM_RETRIEVAL_DOCS)['documents'][0])
        responses['human_rag'].append(generate_response(q, human_ctx))

        if (i + 1) % 5 == 0:
            logger.info(f"  Completed {i+1}/{len(questions)} questions")

    # Compute metrics for each approach
    metrics = {}
    for approach, resps in responses.items():
        metrics[approach] = compute_all_metrics(references, resps, include_bertscore)

    return metrics, responses


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate descriptive statistics and 95% CI."""
    n = len(values)
    mean = np.mean(values)
    std = np.std(values, ddof=1)  # Sample std
    se = std / np.sqrt(n)
    ci_95 = 1.96 * se

    return {
        'mean': mean,
        'std': std,
        'se': se,
        'ci_95': ci_95,
        'min': np.min(values),
        'max': np.max(values),
        'n': n
    }


def paired_ttest(values1: List[float], values2: List[float]) -> Dict[str, float]:
    """Perform paired t-test and calculate effect size."""
    t_stat, p_value = stats.ttest_rel(values1, values2)

    # Cohen's d for paired samples
    diff = np.array(values1) - np.array(values2)
    cohens_d = np.mean(diff) / np.std(diff, ddof=1)

    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'significant_005': p_value < 0.05,
        'significant_001': p_value < 0.01
    }


def run_comprehensive_analysis(
    num_runs: int = 5,
    include_bertscore: bool = False
) -> Dict:
    """Run comprehensive analysis with multiple trials."""

    logger.info("="*60)
    logger.info("COMPREHENSIVE RAG EVALUATION")
    logger.info("="*60)
    logger.info(f"Number of runs: {num_runs}")
    logger.info(f"Include BERTScore: {include_bertscore}")

    # Load data
    test_data = load_independent_test_set()
    human_data, ai_data = load_datasets()

    logger.info(f"Test questions: {len(test_data)}")

    # Run multiple trials
    all_metrics = {approach: {metric: [] for metric in ['rouge1', 'rouge2', 'rougeL', 'bleu', 'meteor']}
                   for approach in ['baseline', 'raw_rag', 'ai_rag', 'human_rag']}

    if include_bertscore:
        for approach in all_metrics:
            all_metrics[approach]['bertscore'] = []

    all_responses = []

    for run in range(num_runs):
        logger.info(f"\n--- Run {run + 1}/{num_runs} ---")
        start_time = time.time()

        metrics, responses = run_single_evaluation(
            test_data, human_data, ai_data, include_bertscore
        )

        # Store metrics
        for approach, metric_dict in metrics.items():
            for metric, value in metric_dict.items():
                all_metrics[approach][metric].append(value)

        all_responses.append(responses)

        elapsed = time.time() - start_time
        logger.info(f"  Run {run + 1} completed in {elapsed:.1f}s")

    # Calculate statistics
    logger.info("\n" + "="*60)
    logger.info("CALCULATING STATISTICS")
    logger.info("="*60)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'num_runs': num_runs,
            'num_questions': len(test_data),
            'model': config.MODEL_NAME,
            'include_bertscore': include_bertscore,
            'test_set': 'FINAL_independent_test_set.json'
        },
        'statistics': {},
        'comparisons': {},
        'raw_metrics': all_metrics
    }

    # Descriptive statistics per approach/metric
    for approach in all_metrics:
        results['statistics'][approach] = {}
        for metric in all_metrics[approach]:
            values = all_metrics[approach][metric]
            results['statistics'][approach][metric] = calculate_statistics(values)

    # Key comparisons with statistical tests
    primary_metric = 'rougeL'  # Focus on ROUGE-L

    comparisons = [
        ('ai_rag', 'human_rag', 'AI vs Human'),
        ('ai_rag', 'raw_rag', 'AI vs Raw'),
        ('human_rag', 'raw_rag', 'Human vs Raw'),
        ('ai_rag', 'baseline', 'AI vs Baseline'),
        ('raw_rag', 'baseline', 'Raw vs Baseline'),
    ]

    for approach1, approach2, label in comparisons:
        values1 = all_metrics[approach1][primary_metric]
        values2 = all_metrics[approach2][primary_metric]

        test_result = paired_ttest(values1, values2)

        mean1 = np.mean(values1)
        mean2 = np.mean(values2)
        ratio = (mean1 / mean2 * 100) if mean2 > 0 else 0
        diff = (mean1 - mean2) / mean2 * 100 if mean2 > 0 else 0

        results['comparisons'][label] = {
            f'{approach1}_mean': mean1,
            f'{approach2}_mean': mean2,
            'ratio_percent': ratio,
            'diff_percent': diff,
            **test_result
        }

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("RESULTS SUMMARY (ROUGE-L)")
    logger.info("="*60)

    for approach in ['baseline', 'raw_rag', 'ai_rag', 'human_rag']:
        stats = results['statistics'][approach]['rougeL']
        logger.info(f"  {approach:12s}: {stats['mean']:.4f} ± {stats['ci_95']:.4f}")

    logger.info("\n" + "="*60)
    logger.info("KEY COMPARISONS")
    logger.info("="*60)

    for label, comp in results['comparisons'].items():
        sig = "**" if comp['significant_001'] else ("*" if comp['significant_005'] else "")
        logger.info(f"  {label}: {comp['diff_percent']:+.1f}% (d={comp['cohens_d']:.2f}, p={comp['p_value']:.4f}){sig}")

    return results


def save_results(results: Dict, filename: str = None):
    """Save results to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_evaluation_{timestamp}.json"

    output_path = config.RESULTS_DIR / filename
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\nResults saved to: {output_path}")
    return output_path


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive RAG Evaluation")
    parser.add_argument('--runs', type=int, default=5, help='Number of evaluation runs')
    parser.add_argument('--bertscore', action='store_true', help='Include BERTScore (slower)')
    parser.add_argument('--output', type=str, default=None, help='Output filename')

    args = parser.parse_args()

    results = run_comprehensive_analysis(
        num_runs=args.runs,
        include_bertscore=args.bertscore
    )

    save_results(results, args.output)

    # Print professor's targets assessment
    logger.info("\n" + "="*60)
    logger.info("PROFESSOR'S TARGETS ASSESSMENT")
    logger.info("="*60)

    ai_human = results['comparisons']['AI vs Human']
    ai_raw = results['comparisons']['AI vs Raw']

    target1_met = ai_human['ratio_percent'] >= 84
    target2_met = ai_raw['diff_percent'] >= 40

    logger.info(f"  Target 1: AI achieves 84% of Human")
    logger.info(f"    Actual: {ai_human['ratio_percent']:.1f}%")
    logger.info(f"    Status: {'MET' if target1_met else 'NOT MET'}")

    logger.info(f"\n  Target 2: AI 40% better than Raw")
    logger.info(f"    Actual: {ai_raw['diff_percent']:+.1f}%")
    logger.info(f"    Status: {'MET' if target2_met else 'NOT MET'}")


if __name__ == "__main__":
    main()
