# ACL BioNLP 2026 Workshop Submission Instructions

## Overview

This is a **backup submission** to ACL BioNLP 2026 workshop. Submit this if PLOS Digital Health rejects or as a secondary venue for broader dissemination.

## Key Dates

- **Submission Deadline:** April 17, 2026 (11 weeks from now)
- **Notification:** May 4, 2026 (3 weeks after submission)
- **Camera-Ready Due:** May 25, 2026
- **Workshop Date:** July 3-4, 2026 (San Diego, CA)

## Page Limit

- **Main paper:** 8 pages (excluding references)
- **References:** Unlimited pages
- **Appendix:** Unlimited (but reviewers may not read)

## Current Status

✅ **Draft completed:** `acl_manuscript.tex` (8 pages)
⏳ **Waiting period:** Submit in Week 2-4 while PLOS is in review
📅 **Decision point:** If PLOS rejects or major revisions required, submit to ACL immediately

## Condensation Summary

The ACL version condenses the 12-page PLOS manuscript to 8 pages by:

**Kept (4 pages):**
- Introduction (1 page) - Data leakage discovery as hook
- Methodology (2 pages) - Independent test set creation
- Results (1 page) - Main ROUGE-L table + statistical tests

**Condensed (3 pages):**
- Related Work (0.5 pages) - Key citations only
- Discussion (1.5 pages) - Domain saturation hypothesis
- Limitations (0.5 pages) - Bullet point list
- Conclusion (0.5 pages) - Key contributions only

**Moved to Appendix:**
- Complete metrics table (ROUGE-1, ROUGE-2, BLEU, METEOR)
- Example test questions
- Sensitivity analyses
- Detailed statistical tables

**Figures:**
- Kept in-text: Table 1 (contamination), Table 2 (main results), Table 3 (statistics)
- Available in supplementary: All original figures

## Files in This Directory

```
acl_bionlp_2026/
├── acl_manuscript.tex           # Main paper (8 pages)
├── custom.bib                    # References
├── ACL_SUBMISSION_INSTRUCTIONS.md  # This file
└── [TO ADD] acl.sty              # ACL style file (download)
```

## Before Submitting

### 1. Download ACL Style Files

```bash
cd results/acl_bionlp_2026

# Option A: From GitHub
wget https://github.com/acl-org/acl-style-files/archive/refs/heads/master.zip
unzip master.zip
cp acl-style-files-master/acl.sty .
cp acl-style-files-master/acl_natbib.bst .

# Option B: From Overleaf (if using Overleaf)
# Template automatically includes style files
```

### 2. Compile LaTeX

```bash
# Standard compilation
pdflatex acl_manuscript.tex
bibtex acl_manuscript
pdflatex acl_manuscript.tex
pdflatex acl_manuscript.tex

# Check page count
pdfinfo acl_manuscript.pdf | grep Pages
# Expected output: Pages: 10 (8 pages + 2 references + appendix)
```

### 3. Verify Formatting

**ACL Requirements:**
- [ ] Uses `\documentclass[11pt]{article}` with `\usepackage[hyperref]{acl}`
- [ ] Times or equivalent font (11pt)
- [ ] Paper size: US Letter (8.5" x 11")
- [ ] Main content ≤ 8 pages (excluding references)
- [ ] References use `acl_natbib.bst` style
- [ ] Anonymized for review (no author names in submission)

**For Anonymous Submission:**
Edit line 14-18 of `acl_manuscript.tex`:

```latex
% BEFORE SUBMISSION: Anonymize!
\author{Anonymous ACL BioNLP 2026 Submission}

% AFTER ACCEPTANCE: De-anonymize
% \author{Research Team \\
%   Department of Computer Science \\
%   University Name \\
%   \texttt{email@university.edu}}
```

### 4. Update with Latest Results

If you run additional experiments before April 17:
- Update Table 2 (main results)
- Update Table 3 (statistical comparisons)
- Add footnote mentioning arXiv preprint (if allowed)

## Submission Process

### Step 1: Create ACL Anthology Account

1. Go to https://softconf.com/
2. Register with institutional email
3. Activate account

### Step 2: Access BioNLP 2026 Submission Portal

**Portal will be available ~6 weeks before deadline (March 2026)**

Likely URL (check BioNLP workshop website):
- https://softconf.com/acl2026/bionlp2026/

### Step 3: Submit Paper

**Required Fields:**
- **Title:** Evaluation of RAG Knowledge Bases for Smoking Cessation Counseling: A Data Leakage Warning
- **Abstract:** (Same as in paper, ~150 words)
- **Authors:** List all authors with affiliations
- **Keywords:** RAG, retrieval-augmented generation, data leakage, smoking cessation, digital health, NLP evaluation
- **Track:** Research (short paper)
- **Area:** NLP for Healthcare / Question Answering

**Files to Upload:**
- `acl_manuscript.pdf` (main paper, anonymized)
- `acl_manuscript.tex` (source, optional but recommended)
- `custom.bib` (references, optional)

**Submission Form Fields:**

**Primary Subject Area:**
- NLP Applications: Healthcare

**Secondary Subject Areas:**
- Evaluation Methodologies
- Question Answering
- Information Retrieval

**Research Type:**
- Empirical
- Methodological

**Does this paper contain original work?**
- Yes

**Has this work been published elsewhere?**
- No (if PLOS is still under review)
- Yes, preprint on arXiv (provide link)

**Conflicts of Interest:**
- List reviewers who should NOT review (e.g., collaborators, institution colleagues)

**Responsible NLP Statement:**
If required, add section to paper:
```latex
\section*{Ethics Statement}
This research uses publicly available data and does not involve human subjects. All materials are released under open licenses. We acknowledge potential bias in LLM training data but note our focus is on evaluation methodology rather than deployment.
```

### Step 4: Review and Submit

1. Preview PDF in submission system
2. Verify anonymization
3. Check that all required fields are complete
4. Submit before deadline: **April 17, 2026**

## Post-Submission

### Expected Timeline

- **April 17, 2026:** Submission deadline
- **April 17 - May 4:** Peer review (3 weeks)
- **May 4, 2026:** Notification
- **May 25, 2026:** Camera-ready deadline
- **July 3-4, 2026:** Workshop presentation

### If Accepted

**Camera-Ready Preparation:**
1. De-anonymize paper (add author names)
2. Address reviewer comments
3. Update with latest results if improved
4. Add acknowledgments
5. Recompile and verify formatting

**Registration:**
- At least one author must register for ACL 2026
- Early registration deadline: ~June 1, 2026
- Workshop-only registration available (~$100-150)

**Presentation:**
- Short papers: 12-15 minute talk + 3 minutes Q&A
- Prepare slides (PDF or PowerPoint)
- Practice timing
- Consider poster as backup

### If Rejected

**Backup Options:**
1. **Scientific Reports** - Nature portfolio, ~60% acceptance
2. **JMIR** (Journal of Medical Internet Research) - Digital health focus
3. **IEEE Access** - Fast review, open access
4. **PLOS ONE** - Broader scope than PLOS Digital Health

**Use reviewer feedback to strengthen:**
- Address methodological concerns
- Add requested experiments
- Expand discussion
- Improve clarity

## Advantages of ACL BioNLP

vs. PLOS Digital Health:
- ✅ **Faster review:** 3 weeks vs. 20 weeks
- ✅ **Prestige in NLP community:** ACL is top-tier
- ✅ **Conference presentation:** Visibility and networking
- ✅ **Guaranteed publication:** If accepted, appears in ACL Anthology

Disadvantages:
- ❌ **Page limit:** 8 pages vs. unlimited for PLOS
- ❌ **Less detail:** Must condense methodology
- ❌ **Cost:** Conference registration required (~$700-900)
- ❌ **Limited audience:** NLP researchers, not clinicians

## Strategic Decision Tree

**Scenario 1: PLOS Accepts (Most Likely)**
- ✅ Publish in PLOS
- ❌ Do NOT submit to ACL BioNLP (duplicate publication)
- ✅ Present findings at relevant conferences as invited talk

**Scenario 2: PLOS Desk Rejects (Unlikely, ~10%)**
- ✅ Submit immediately to ACL BioNLP (have 11 weeks)
- ✅ Address editor concerns in ACL version
- ✅ Also submit to Scientific Reports as backup

**Scenario 3: PLOS Major Revisions (Possible, ~30%)**
- 🤔 Depends on severity of revisions
- Option A: Revise for PLOS, skip ACL (if revisions are minor)
- Option B: Submit to ACL anyway (if revisions are extensive)

**Scenario 4: PLOS Minor Revisions (Most Likely If Not Accepted, ~50%)**
- ✅ Revise for PLOS
- ❌ Skip ACL BioNLP (PLOS likely to accept revised version)

## Contact for Questions

**BioNLP Workshop Organizers:**
- Check workshop website: https://aclweb.org/aclwiki/BioNLP_Workshop
- Email: bionlp-organizers@googlegroups.com (check website for current contact)

**ACL 2026 General:**
- Website: https://2026.aclweb.org/
- Email: acl2026@aclweb.org

## Checklist Before April 17, 2026

- [ ] Downloaded ACL style files (acl.sty, acl_natbib.bst)
- [ ] Compiled PDF successfully
- [ ] Verified page count ≤ 8 pages (excluding references)
- [ ] Anonymized author information
- [ ] Updated results if new experiments run
- [ ] Proofread for typos and clarity
- [ ] Checked all references are formatted correctly
- [ ] Added arXiv link (if allowed)
- [ ] Co-authors approved ACL submission
- [ ] GitHub repo updated with latest materials
- [ ] Prepared 250-word summary for submission form
- [ ] Listed potential conflicts of interest

---

**Status:** Draft ready, awaiting PLOS decision before submitting

**Next Action:** Monitor PLOS review status (Week 3-5). If rejected or major revisions, submit to ACL immediately.
