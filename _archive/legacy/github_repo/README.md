# RAG Evaluation for Smoking Cessation Counseling

[![arXiv](https://img.shields.io/badge/arXiv-2026.XXXXX-b31b1b.svg)](https://arxiv.org/abs/2026.XXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Comprehensive Evaluation of Retrieval-Augmented Generation Knowledge Bases for Smoking Cessation Counseling: A Methodological Warning on Data Leakage**

## 📋 Overview

This repository contains the data, code, and results for our comprehensive evaluation of RAG (Retrieval-Augmented Generation) approaches for smoking cessation counseling. Our research makes two primary contributions:

### Methodological Contribution
**Data Leakage Discovery:** We discovered severe contamination in our original test set—47% of questions had ≥90% similarity to training data, including four exact matches (100%). This data leakage completely reversed our initial conclusions, serving as a critical warning for NLP evaluation research.

### Empirical Findings
- **Baseline outperforms RAG:** The no-retrieval baseline achieved higher ROUGE-L scores (0.231) than all RAG variants, suggesting domain-dependent RAG benefit
- **AI-generated equals human-curated:** AI-generated knowledge bases performed comparably to expert-curated ones (102.1% relative performance, p=0.184)
- **Structured beats raw:** Both AI and human-curated RAG significantly outperformed raw sources (p<0.05)

## 🔑 Key Results

| Approach | ROUGE-L | BLEU | METEOR |
|----------|---------|------|--------|
| **Baseline (No RAG)** | **0.231 ± 0.008** | 0.054 ± 0.004 | 0.310 ± 0.010 |
| AI-Generated RAG | 0.224 ± 0.005 | **0.057 ± 0.003** | 0.290 ± 0.008 |
| Human-Curated RAG | 0.220 ± 0.004 | 0.045 ± 0.003 | 0.296 ± 0.010 |
| Raw Sources RAG | 0.208 ± 0.004 | 0.039 ± 0.003 | 0.275 ± 0.008 |

*Values shown as mean ± 95% CI (5 runs, 15 questions each)*

## 📊 Data Leakage Impact

**Original Test Set Contamination:**
- Severe (≥90% similarity): **7 questions (47%)**
- Moderate (70-90% similarity): 6 questions (40%)
- Clean (<70% similarity): 2 questions (13%)
- **Exact matches (100%)**: 4 questions (27%)

The contaminated test set showed a **completely reversed ranking**: Raw > Human > AI (wrong), vs. the true ranking: Baseline > AI > Human > Raw (correct).

## 📁 Repository Structure

```
.
├── data/
│   └── FINAL_independent_test_set.json    # 15 validated test questions
├── scripts/
│   └── comprehensive_rag_evaluation.py     # Full evaluation pipeline
├── results/
│   └── comprehensive_results.json          # Complete experimental results
├── requirements.txt                        # Python dependencies
├── README.md                               # This file
└── LICENSE                                 # MIT License
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/[username]/rag-smoking-cessation-eval.git
cd rag-smoking-cessation-eval

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

### Running the Evaluation

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Run the comprehensive evaluation
python scripts/comprehensive_rag_evaluation.py
```

**Expected runtime:** ~15-20 minutes (5 runs × 15 questions × 4 approaches = 300 API calls)

**Expected cost:** ~$0.50-1.00 (using GPT-4o-mini at $0.15/1M input tokens, $0.60/1M output tokens)

## 📖 Methodology

### Independent Test Set Creation

To ensure zero data leakage, we created a new test set with:
- **Similarity threshold:** <50% fuzzy string match to any training question
- **Validation method:** `SequenceMatcher` from Python's `difflib`
- **Sample size:** 15 questions covering diverse topics
- **Topic coverage:** Benefits (immediate, long-term), cravings, NRT, withdrawal, relapse, addiction mechanisms, supporting others

See `data/FINAL_independent_test_set.json` for the complete validated test set.

### Evaluation Protocol

- **Model:** GPT-4o-mini (temperature=0.3, max_tokens=200)
- **Retrieval:** ChromaDB with cosine similarity, k=3 documents
- **Runs:** 5 independent trials per approach
- **Metrics:** ROUGE-L (primary), ROUGE-1/2, BLEU, METEOR
- **Statistics:** 95% confidence intervals, paired t-tests, Cohen's d effect sizes

### Approaches Compared

1. **Baseline (No RAG):** Direct LLM responses without retrieval
2. **Raw Sources RAG:** Retrieval from unprocessed source documents
3. **AI-Generated RAG:** Retrieval from GPT-4-generated Q&A pairs
4. **Human-Curated RAG:** Retrieval from expert-curated Q&A database

## 📈 Statistical Comparisons (ROUGE-L)

| Comparison | Difference | Cohen's d | p-value | Significant |
|------------|------------|-----------|---------|-------------|
| AI vs Human | +2.1% | 0.72 | 0.184 | No |
| AI vs Raw | +7.8% | 3.19 | **0.002** | **Yes*** |
| Human vs Raw | +5.5% | 1.89 | **0.014** | **Yes** |
| AI vs Baseline | -2.6% | -1.07 | 0.074 | No |
| Raw vs Baseline | -9.7% | -3.25 | **0.002** | **Yes*** |

*p < 0.05, **p < 0.01

## 🔍 Reproducing Results

### Verify Data Leakage Detection

```python
import json
from difflib import SequenceMatcher

# Load test set
with open('data/FINAL_independent_test_set.json') as f:
    test_data = json.load(f)['test_data']

# Check similarity against your training data
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

for test_q in test_data:
    for train_q in your_training_questions:
        sim = similarity(test_q['question'], train_q)
        if sim >= 0.5:
            print(f"WARNING: {sim:.1%} similarity detected")
```

### Load Pre-Computed Results

```python
import json

# Load complete results
with open('results/comprehensive_results.json') as f:
    results = json.load(f)

# Access statistics
print(results['statistics']['baseline']['rougeL'])
# Output: {'mean': 0.231, 'ci_95': 0.008, ...}

# Access comparisons
print(results['comparisons']['AI vs Human']['p_value'])
# Output: 0.184
```

### Custom Evaluation

```python
from scripts.comprehensive_rag_evaluation import (
    load_independent_test_set,
    generate_response,
    compute_rouge
)

# Load test questions
test_questions = load_independent_test_set()

# Generate responses
for q in test_questions:
    response = generate_response(q['question'])
    scores = compute_rouge(q['reference'], response)
    print(f"ROUGE-L: {scores['rougeL']:.3f}")
```

## 💡 Key Takeaways

### For Researchers
1. **Always validate test sets:** Use fuzzy string matching to detect data leakage
2. **Recommended threshold:** <50% similarity for question-answering tasks
3. **Report similarity distributions:** Include in supplementary materials
4. **Baseline is critical:** RAG is not universally beneficial

### For Practitioners
1. **Domain matters:** For well-documented topics, RAG may not help
2. **AI generation works:** Can match human curation at lower cost
3. **Structure helps:** Structured knowledge beats raw sources
4. **Test before deploying:** Measure baseline vs. RAG performance on your specific domain

## 🎯 Domain Saturation Hypothesis

We propose that RAG benefit is **inversely related to domain representation in LLM training data**:

- **High saturation** (e.g., smoking cessation) → Baseline sufficient, RAG may hurt
- **Medium saturation** → RAG provides marginal improvement
- **Low saturation** (e.g., rare diseases, emerging treatments) → RAG critical

**Future work** should test this hypothesis across domains with varying LLM knowledge coverage.

## 📝 Citation

If you use this dataset, code, or findings in your research, please cite:

```bibtex
@article{author2026rag,
  title={Comprehensive Evaluation of Retrieval-Augmented Generation Knowledge Bases for Smoking Cessation Counseling: A Methodological Warning on Data Leakage},
  author={[Authors]},
  journal={PLOS Digital Health},
  year={2026},
  url={https://github.com/[username]/rag-smoking-cessation-eval}
}
```

**arXiv preprint:** [https://arxiv.org/abs/2026.XXXXX](https://arxiv.org/abs/2026.XXXXX)

## 🛠️ Technical Details

### Dependencies

- Python 3.8+
- OpenAI API key
- See `requirements.txt` for complete list

### Hardware Requirements

- **Minimal:** Any modern laptop (evaluation runs on CPU)
- **RAM:** 4GB+ recommended
- **Storage:** <100MB for data and results

### API Costs

Approximate costs using GPT-4o-mini:
- **Single run:** $0.10-0.20
- **Full evaluation (5 runs):** $0.50-1.00
- **With BERTScore:** +$0.00 (runs locally on CPU)

## 🐛 Known Issues

1. **BERTScore optional:** Requires `bert-score` package, adds ~2-3x runtime
2. **NLTK downloads:** Must manually download `punkt` and `wordnet` corpora
3. **API rate limits:** Add delays between calls if hitting OpenAI rate limits

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

**Areas for contribution:**
- Testing on other domains (rare diseases, legal advice, etc.)
- Additional RAG architectures (ColBERT, dense passage retrieval, etc.)
- Human evaluation protocols
- Additional metrics (semantic similarity, factual accuracy, etc.)

## 📧 Contact

For questions or collaboration inquiries:
- **Email:** [author@institution.edu]
- **GitHub Issues:** [https://github.com/[username]/rag-smoking-cessation-eval/issues](https://github.com/[username]/rag-smoking-cessation-eval/issues)

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Professor [Name] for guidance throughout this research
- Domain experts who validated test questions
- OpenAI for API access
- PLOS Digital Health for open-access publication

## 📚 Related Work

- **Data Leakage in NLP:** [Lewis et al., EACL 2021](https://aclanthology.org/2021.eacl-main.86/)
- **RAG Systems:** [Lewis et al., NeurIPS 2020](https://arxiv.org/abs/2005.11401)
- **Smoking Cessation Guidelines:** [Fiore et al., 2008](https://www.ahrq.gov/prevention/guidelines/tobacco/index.html)

---

**Last updated:** January 19, 2026

**Repository status:** ✅ Active | 📊 Results validated | 🔓 Open source | 📖 Documented
