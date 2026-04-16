# GitHub Repository Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the **"+"** icon in top right → **"New repository"**
3. Repository settings:
   - **Repository name:** `rag-smoking-cessation-eval`
   - **Description:** "Evaluation of RAG systems for smoking cessation counseling with data leakage discovery"
   - **Visibility:** ✅ Public
   - **Initialize:**
     - ❌ Do NOT add README (we have one)
     - ❌ Do NOT add .gitignore (we have one)
     - ✅ Add MIT License (or skip, we have one)
4. Click **"Create repository"**

## Step 2: Initialize Local Repository

```bash
# Navigate to the github_repo directory
cd results/github_repo

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial release: RAG evaluation with data leakage discovery

- Independent test set with <50% similarity validation
- Comprehensive evaluation results (5 runs, statistical testing)
- Full reproduction code with ChromaDB and OpenAI API
- Detailed README with methodology and results
- MIT License for open use"

# Add remote (replace [username] with your GitHub username)
git remote add origin https://github.com/[username]/rag-smoking-cessation-eval.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Configure Repository Settings

### Add Topics
Go to repository → **"About"** → **"Topics"**:
- `rag`
- `retrieval-augmented-generation`
- `nlp`
- `smoking-cessation`
- `data-leakage`
- `evaluation`
- `digital-health`
- `reproducible-research`

### Create Release

1. Go to **"Releases"** → **"Create a new release"**
2. Tag version: `v1.0.0`
3. Release title: `v1.0.0 - Initial Public Release`
4. Description:
```markdown
## Initial Release

**Publication:** "Comprehensive Evaluation of RAG Knowledge Bases for Smoking Cessation Counseling"

### Key Features
✅ Independent test set (15 questions, <50% similarity validated)
✅ Complete evaluation results (5 runs, 4 approaches)
✅ Reproduction scripts with ChromaDB + OpenAI API
✅ Comprehensive documentation

### Data Leakage Discovery
⚠️ Found 47% severe contamination in original test set (7/15 questions ≥90% similarity)
⚠️ Data leakage completely reversed conclusions

### Results
- Baseline: 0.231 ROUGE-L (best)
- AI-Generated RAG: 0.224 ROUGE-L
- Human-Curated RAG: 0.220 ROUGE-L
- Raw Sources RAG: 0.208 ROUGE-L

### Files
- `data/FINAL_independent_test_set.json` - Validated test set
- `results/comprehensive_results.json` - Full experimental results
- `scripts/comprehensive_rag_evaluation.py` - Reproduction code

### Citation
```bibtex
@article{author2026rag,
  title={Comprehensive Evaluation of RAG Knowledge Bases...},
  author={[Authors]},
  journal={PLOS Digital Health},
  year={2026}
}
```

**arXiv:** https://arxiv.org/abs/2026.XXXXX
```

5. Click **"Publish release"**

## Step 4: Enable Features

### Enable Discussions
Settings → Features → ✅ Discussions

Create discussion categories:
- 💬 General
- 💡 Ideas
- 🙏 Q&A
- 📣 Announcements

### Enable Issues
Settings → Features → ✅ Issues

Create issue templates:
1. **Bug Report**
2. **Feature Request**
3. **Reproduction Question**

### Add Repository Description
Settings → Description:
```
Comprehensive RAG evaluation for smoking cessation counseling. Discovered 47% test set contamination, demonstrating critical importance of data leakage validation. Baseline outperforms RAG for well-documented domains.
```

## Step 5: Add Documentation

### Create Wiki (Optional)
Wiki → Create first page:
- **Home:** Overview and navigation
- **Methodology:** Detailed evaluation protocol
- **Results:** Complete findings with visualizations
- **FAQ:** Common questions about reproduction

### Add README Badges
Add to top of README.md:
```markdown
[![GitHub release](https://img.shields.io/github/v/release/[username]/rag-smoking-cessation-eval)](https://github.com/[username]/rag-smoking-cessation-eval/releases)
[![GitHub stars](https://img.shields.io/github/stars/[username]/rag-smoking-cessation-eval)](https://github.com/[username]/rag-smoking-cessation-eval/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

## Step 6: Share and Promote

### Update Paper References
Replace `[username]` in:
- `results/plos_submission/plos_manuscript.tex`
- `results/plos_submission/cover_letter.tex`
- `results/github_repo/README.md`
- `results/github_repo/CITATION.cff`

### Announce on Social Media
**Twitter/X template:**
```
🚨 New research alert: We found 47% of our test set was contaminated!

Data leakage completely reversed our RAG evaluation conclusions.

📊 Surprising finding: Baseline > RAG for well-known domains
📝 Paper: [arXiv link]
💻 Code & Data: [GitHub link]

Thread 🧵👇
```

**LinkedIn template:**
```
We just published our research on RAG evaluation for smoking cessation counseling, and discovered a critical methodological issue:

⚠️ 47% of questions in our original test set were severely contaminated (≥90% similarity to training data)

This data leakage completely reversed our conclusions about which RAG approaches performed best.

Key findings:
✅ For well-documented domains, baseline LLMs may outperform RAG
✅ AI-generated knowledge bases match human-curated ones (102% relative performance)
✅ Test set independence validation is critical but often overlooked

All data, code, and results are open source.

Paper: [arXiv link]
Code: [GitHub link]

#NLP #MachineLearning #DigitalHealth #OpenScience
```

## Step 7: Link to arXiv

After arXiv submission:
1. Update README.md with arXiv URL
2. Update CITATION.cff with DOI
3. Add arXiv badge to README
4. Create new GitHub release (v1.0.1) with updated links

## Verification Checklist

Before making public:
- [ ] All `[username]` placeholders replaced
- [ ] All `[Author Name]` placeholders replaced
- [ ] .env file NOT included in repository
- [ ] API keys NOT exposed in code or git history
- [ ] README instructions tested on fresh environment
- [ ] All links work (no 404s)
- [ ] License file present
- [ ] CITATION.cff file present
- [ ] .gitignore file present
- [ ] Scripts run without errors (test locally first)

## Maintenance

### Keep Updated
- Update arXiv link when paper is posted
- Update DOI when paper is published
- Respond to issues within 48 hours
- Add FAQ section based on common questions

### After Publication
Create announcement:
```markdown
## 🎉 Paper Published!

Our paper has been published in PLOS Digital Health:

**DOI:** https://doi.org/10.1371/journal.pdig.XXXXXXX

All materials remain open source under MIT License.

Thank you to everyone who contributed, shared, and provided feedback!
```

---

**Questions?** Open an issue or discussion on GitHub.
