# arXiv Submission Guide

## Overview

Submit the manuscript to arXiv for immediate public visibility and to establish priority for your findings, especially the data leakage discovery.

**Benefits of arXiv:**
- ✅ Immediate public visibility (same day)
- ✅ Citable with DOI before journal publication
- ✅ Standard practice in AI/ML community
- ✅ Free (no submission fees)
- ✅ Builds early citations
- ✅ Can be updated with revisions

## Pre-Submission Checklist

Before submitting to arXiv:
- [ ] GitHub repository is public
- [ ] All author names and affiliations finalized
- [ ] Co-authors have approved submission
- [ ] Abstract is under 1920 characters (arXiv limit)
- [ ] PDF renders correctly (no missing figures)
- [ ] References are formatted properly
- [ ] GitHub URL included in abstract or footnote

## Step 1: Create arXiv Account

1. Go to [arXiv.org](https://arxiv.org)
2. Click **"register"** (top right)
3. Complete registration with institutional email (preferred for endorsement)
4. Verify email address

## Step 2: Get Endorsement (If Needed)

**If you're a first-time submitter:**
- arXiv requires endorsement in cs.CL (Computation and Language) or cs.AI
- Request endorsement from advisor or collaborator who has submitted to cs.CL before
- Alternative: Submit to stat.ML (Machine Learning) which may not require endorsement

**Check if you need endorsement:**
- Go to arXiv → **"Submit"** → Select category cs.CL
- System will tell you if you need endorsement

## Step 3: Prepare Files

### Primary File: PDF
- **File:** `arxiv_manuscript.pdf`
- **Size:** 171 KB (✅ under arXiv's 10 MB limit)
- **Format:** PDF/A compatible

### Optional: LaTeX Source
If you want to include LaTeX source for reproducibility:
- Copy `results/plos_submission/plos_manuscript.tex`
- Include all figure PDFs
- Create a .tar.gz archive

```bash
cd results/plos_submission
tar -czf arxiv_source.tar.gz plos_manuscript.tex *.pdf
```

**Recommendation:** Submit PDF only for first version. Source can be added later if requested.

## Step 4: Submit to arXiv

### Navigate to Submission Portal
1. Log into arXiv
2. Click **"Submit"** in top right
3. Follow the step-by-step form

### Step 4.1: Select Archive and Subject Class

**Primary category:**
- `cs.CL` - Computation and Language (BEST FIT)
  - Reason: NLP evaluation methodology, text generation

**Alternative primary categories:**
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning

**Cross-list to (optional but recommended):**
- `cs.AI` - Artificial Intelligence
- `stat.ML` - Machine Learning (Statistics)

### Step 4.2: Enter Metadata

**Title:**
```
Comprehensive Evaluation of Retrieval-Augmented Generation Knowledge Bases for Smoking Cessation Counseling: A Methodological Warning on Data Leakage
```

**Authors:**
```
[First Author Name] ([Institution])
[Second Author Name] ([Institution])
```

**Abstract:**
```
We present a rigorous comparison of Retrieval-Augmented Generation (RAG) approaches for smoking cessation counseling using an independent test set validated for zero data leakage. Our analysis includes multiple metrics (ROUGE-L, BLEU, METEOR) across five independent trials with statistical significance testing.

Contrary to expectations, the baseline approach (no retrieval) outperformed all RAG variants (ROUGE-L: 0.231 vs 0.224 for best RAG), suggesting that for well-documented domains like smoking cessation, LLM parametric knowledge may be sufficient. Among RAG approaches, AI-generated knowledge bases slightly exceeded human-curated ones (102.1% relative performance, p=0.184).

Critically, we discovered severe data leakage in the original test set: 47% of questions had ≥90% similarity to training data, including four exact matches (100%). This contamination completely reversed our initial conclusions, demonstrating the importance of rigorous test set independence verification in NLP research.

Our findings shift the research question from "Does RAG help?" to "When does RAG help?"—proposing that RAG benefit is domain-dependent and may be inversely related to topic representation in LLM training data.

Code and data: https://github.com/[username]/rag-smoking-cessation-eval
```

**Character count:** ~1,350 (✅ under 1,920 limit)

**Comments (optional):**
```
15 pages, 5 tables. Submitted to PLOS Digital Health. All data and code publicly available.
```

**Journal reference (optional):**
```
Submitted to PLOS Digital Health, January 2026
```

**Report number:** Leave blank

**MSC class / ACM class:** Leave blank

**DOI:** Leave blank (will be assigned by arXiv)

### Step 4.3: Upload Files

1. Click **"Choose File"** → Select `arxiv_manuscript.pdf`
2. arXiv will process the file (takes 1-2 minutes)
3. Verify that PDF displays correctly in preview
4. If there are errors, fix and re-upload

### Step 4.4: Add Metadata

**License:**
- Select: `arXiv.org perpetual, non-exclusive license to distribute`
- (This is standard and allows journal publication)

**Copyright:**
- If you will publish in PLOS (open access), select:
  - `Creative Commons Attribution 4.0 International (CC BY 4.0)`

### Step 4.5: Preview and Submit

1. Review all information carefully
2. Check author order
3. Verify abstract formatting
4. Click **"Submit"**

## Step 5: Post-Submission Process

### Announcement Process
- **Sunday-Thursday submissions:** Announced next day at 20:00 ET (8 PM Eastern Time)
- **Friday submissions:** Announced following Tuesday at 20:00 ET
- You'll receive email confirmation when live

### Your arXiv URL Will Be:
```
https://arxiv.org/abs/YYMM.NNNNN
```
Where:
- `YY` = Year (26)
- `MM` = Month (01, 02, etc.)
- `NNNNN` = Sequential number

**Example:** `https://arxiv.org/abs/2601.12345`

### Citations Will Use:
```bibtex
@article{author2026rag,
  title={Comprehensive Evaluation of RAG Knowledge Bases...},
  author={[Authors]},
  journal={arXiv preprint arXiv:2601.NNNNN},
  year={2026},
  url={https://arxiv.org/abs/2601.NNNNN}
}
```

## Step 6: After arXiv Goes Live

### Immediate Actions (Same Day)

**1. Update GitHub Repository**
```bash
cd results/github_repo

# Update README.md with arXiv link
# Replace: [![arXiv](https://img.shields.io/badge/arXiv-2026.XXXXX-b31b1b.svg)](https://arxiv.org/abs/2026.XXXXX)
# With: [![arXiv](https://img.shields.io/badge/arXiv-2601.NNNNN-b31b1b.svg)](https://arxiv.org/abs/2601.NNNNN)

# Update CITATION.cff
# Update README citation section

git add README.md CITATION.cff
git commit -m "Add arXiv preprint link"
git push
```

**2. Update PLOS Submission**
- Add arXiv URL to cover letter footnote
- Reference in manuscript if allowed

**3. Announce on Social Media**

**Twitter/X:**
```
🎉 New preprint on arXiv!

We evaluated RAG for smoking cessation counseling and discovered:

⚠️ 47% of our test set was contaminated (data leakage)
📊 Baseline > RAG for well-known domains
🤖 AI-generated = Human-curated knowledge bases

Paper: https://arxiv.org/abs/2601.NNNNN
Code: https://github.com/[username]/rag-smoking-cessation-eval

Thread 🧵👇

1/ We compared 4 approaches across 5 runs (75 responses per approach):
- Baseline (no RAG): 0.231 ROUGE-L ✅
- AI-Generated RAG: 0.224 ROUGE-L
- Human-Curated RAG: 0.220 ROUGE-L
- Raw Sources RAG: 0.208 ROUGE-L

2/ The data leakage discovery was shocking: 7/15 questions (47%) had ≥90% similarity to training data. Four were EXACT matches (100%). This completely reversed our initial conclusions.

3/ Key takeaway: RAG isn't universally helpful. For well-documented domains, LLM parametric knowledge may suffice. We propose RAG benefit is domain-dependent—inversely related to topic coverage in training data.

4/ Methodological warning: Always validate test sets with fuzzy string matching. Our <50% similarity threshold caught the leakage. Many NLP benchmarks may have similar issues.

5/ All materials are open source:
📊 Independent test set (15 validated questions)
💻 Reproduction code (ChromaDB + OpenAI)
📈 Complete results (5 runs, statistics)

Check it out: https://github.com/[username]/rag-smoking-cessation-eval

Questions? Comments? Let's discuss! 👇
```

**LinkedIn:**
```
🎉 New research preprint: "When Does RAG Actually Help?"

We evaluated Retrieval-Augmented Generation for smoking cessation counseling and made two surprising discoveries:

🔍 DATA LEAKAGE CRISIS
47% of questions in our original test set were severely contaminated (≥90% similarity to training data). Four were exact matches. This completely reversed our conclusions.

📊 BASELINE > RAG
The no-retrieval baseline outperformed all RAG variants (0.231 vs 0.224 ROUGE-L), suggesting RAG benefit is domain-dependent.

🤖 AI = HUMAN KNOWLEDGE BASES
AI-generated knowledge bases performed comparably to expert-curated ones (102% relative performance, p=0.184).

KEY INSIGHT: For well-documented domains like smoking cessation, LLM parametric knowledge may be sufficient. We propose RAG benefit is inversely related to domain representation in training data.

METHODOLOGICAL CONTRIBUTION: This serves as a warning for NLP researchers—test set independence validation is critical but often overlooked.

All materials are open source:
✅ Independent test set (15 validated questions)
✅ Reproduction code (ChromaDB + OpenAI)
✅ Complete results (5 runs with statistics)

📄 arXiv: https://arxiv.org/abs/2601.NNNNN
💻 Code: https://github.com/[username]/rag-smoking-cessation-eval

Thoughts? Experiences with data leakage in your work? Let's discuss in the comments.

#NLP #MachineLearning #RAG #DigitalHealth #OpenScience #Research
```

**4. Email Collaborators**
```
Subject: Our RAG evaluation paper is on arXiv!

Hi team,

Our paper "Comprehensive Evaluation of RAG Knowledge Bases for Smoking Cessation Counseling" is now live on arXiv:

https://arxiv.org/abs/2601.NNNNN

Key highlights:
- Discovered 47% test set contamination (data leakage)
- Baseline outperforms RAG for well-known domains
- AI-generated matches human-curated knowledge bases

The GitHub repo with all data and code is also live:
https://github.com/[username]/rag-smoking-cessation-eval

Please feel free to share widely. Next step is awaiting PLOS Digital Health review.

Thanks for all your contributions!

Best,
[Your Name]
```

**5. Share in Relevant Communities**
- Reddit: r/MachineLearning, r/LanguageTechnology
- Hacker News (may get picked up organically)
- NLP Discord servers
- Academic Twitter
- LinkedIn research groups

## Step 7: Updating the Preprint

### When to Submit Updates

**Before journal acceptance:**
- Major errors discovered
- Significant new results added
- Reviewer feedback incorporated

**How to update:**
1. Go to arXiv → **"Replace"**
2. Upload new PDF
3. Select "This is a minor update"
4. Add brief change log

**Version history will show:**
- v1: January 19, 2026 (original)
- v2: February 15, 2026 (minor corrections)
- v3: April 1, 2026 (reviewer feedback)

### After Journal Publication

When PLOS Digital Health publishes:
1. Submit final version to arXiv
2. Update metadata with:
   - Journal reference: "PLOS Digital Health, DOI: 10.1371/..."
   - DOI: Link to published version
3. Add note: "Accepted manuscript, DOI: ..."

## Troubleshooting

### Common Issues

**1. "Endorsement required"**
- Ask advisor or collaborator to endorse
- Alternative: Try stat.ML or cs.AI categories

**2. "PDF processing failed"**
- Check that all fonts are embedded
- Regenerate PDF with `pdflatex`
- Use PDF/A format

**3. "Abstract too long"**
- arXiv limit: 1920 characters
- Condense without losing key findings
- Move details to main text

**4. "Figures missing"**
- Ensure all figure files included
- Check file paths in LaTeX
- Recompile with figures embedded

**5. "Duplicate submission detected"**
- If previously uploaded to another preprint server
- Contact arXiv moderators: moderation@arxiv.org

## Best Practices

### Timing
- ✅ Submit SAME DAY as PLOS submission
- ✅ Post before conference deadlines
- ✅ Coordinate with co-authors' schedules

### Quality
- ✅ Final proofread before submission
- ✅ Have co-author review one more time
- ✅ Check all links work (GitHub, DOIs, etc.)

### Ethics
- ✅ Ensure all co-authors approve
- ✅ Disclose conflicts of interest
- ✅ Follow journal preprint policies (PLOS allows arXiv)

## Resources

- **arXiv Help:** https://info.arxiv.org/help/
- **Submission Guide:** https://info.arxiv.org/help/submit/index.html
- **Category Descriptions:** https://arxiv.org/category_taxonomy
- **License Info:** https://info.arxiv.org/help/license/index.html

## Post-Publication Checklist

After arXiv goes live:
- [ ] arXiv URL added to GitHub README
- [ ] arXiv URL added to PLOS cover letter
- [ ] CITATION.cff updated with arXiv ID
- [ ] Social media announcements posted
- [ ] Co-authors notified
- [ ] Shared in relevant communities
- [ ] Added to personal CV/website
- [ ] Tracking citations with Google Scholar

---

**Questions?** Email arXiv help: help@arxiv.org

**Ready to submit?** Go to: https://arxiv.org/submit
