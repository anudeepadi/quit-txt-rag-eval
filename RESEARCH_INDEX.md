# QuitTxt Protocol-Guided AI System - Research Documentation Index

**Research Project**: Protocol-Guided Conversational AI for Smoking Cessation Support
**Date**: October 2025
**Status**: Development Complete - Ready for Evaluation

---

## Document Overview

This index provides a roadmap to all research documentation for this project. Each document serves a specific purpose in documenting the system design, development, and evaluation.

---

## Core Research Documents

### 1. **RESEARCH_DOCUMENTATION.md** ⭐ PRIMARY RESEARCH DOC
**Purpose**: Iterative algorithm improvement study
**Content**:
- Problem statement and research objectives
- Baseline approach (Version 1.0) with performance metrics
- Three iterations of improvement with quantitative results
- Statistical analysis (paired t-tests, effect sizes)
- Qualitative content analysis
- Performance benchmarks

**Use For**:
- Methods section of thesis
- Results section with metrics
- Algorithm improvement narrative

**Key Metrics**:
- Precision@1: 0% → 100%
- Target section scores: +633% improvement
- Therapeutic content: 18.3% → 91.8%
- Statistical significance: p < 0.001, Cohen's d = 3.71

---

### 2. **RAG_APPROACH.md** ⭐ TECHNICAL ARCHITECTURE DOC
**Purpose**: Retrieval-Augmented Generation methodology
**Content**:
- RAG system architecture (Retrieval → Augmentation → Generation)
- Protocol fidelity vs. conversational quality trade-off
- System prompt engineering evolution
- Comparison to alternative approaches (fine-tuning, rule-based, pure LLM)
- Evaluation metrics for both protocol adherence and conversational quality
- Best practices for health intervention RAG

**Use For**:
- Background/related work section
- Technical approach description
- Discussion of design decisions
- Future work implications

**Key Concepts**:
- In-context learning
- Protocol as knowledge source, not template
- Balanced RAG design
- Multi-objective optimization (accuracy + naturalness)

---

### 3. **DEPLOYMENT_GUIDE.md**
**Purpose**: System setup and usage instructions
**Content**:
- Complete setup procedures
- Testing recommendations (4 phases over 4 weeks)
- Metrics to track
- Customization guide
- Troubleshooting

**Use For**:
- Reproducibility section
- User study protocols
- System deployment documentation

---

### 4. **README.md**
**Purpose**: Project overview and quick start
**Content**:
- Architecture diagram
- Installation instructions
- API endpoints
- Integration guide for Flutter app
- How it works (protocol context manager)

**Use For**:
- Introduction/overview
- System architecture section
- Implementation details

---

### 5. **CLAUDE.md**
**Purpose**: Developer guide for future maintenance
**Content**:
- Development commands
- Key customization points
- Common issues and solutions
- File responsibilities
- Current model configuration (Gemini 2.0 Flash)

**Use For**:
- Implementation details
- Reproducibility
- Future work recommendations

---

## Source Code Documentation

### Core Modules

#### **protocol_manager.py** (244 lines)
**Purpose**: Protocol retrieval and relevance scoring

**Key Components**:
1. **Section Parsing** (lines 33-85)
   - Pattern-based header detection
   - Minimum content thresholds
   - 188 sections extracted from 142KB protocol

2. **Keyword Extraction** (lines 87-107)
   - 28 smoking cessation terms
   - Binary presence detection
   - Expanded to include strategy terms (breathe, distract, 4 Ds)

3. **Relevance Scoring** (lines 163-239)
   - 6-component algorithm:
     - Direct keyword matching (+5.0)
     - Message term coverage (+2.0)
     - Bidirectional topic matching (+3.0 or +0.5)
     - Title matching (+4.0 to +10.0)
     - Critical strategy boosting (+20.0 for 4 Ds)
   - Content-aware scoring

4. **Smart Context Extraction** (lines 140-175)
   - 2000 character limit per section
   - Intelligent positioning for critical strategies
   - Prevents truncation of important content

**Research Value**:
- Algorithm implementation details
- Scoring function evolution
- Performance characteristics

---

#### **api_server.py** (202 lines)
**Purpose**: FastAPI backend with Gemini integration

**Key Components**:
1. **System Prompt Engineering** (lines 122-151)
   - RAG instructions
   - Balance between protocol fidelity and conversational quality
   - Anti-repetition guidelines
   - Personalization directives

2. **Prompt Construction** (lines 153-165)
   - Protocol context injection
   - Conversation history management (last 5 messages)
   - Structured input format

3. **API Endpoints**:
   - `/chat` - Single response generation
   - `/chat/compare` - Side-by-side protocol vs. no-protocol
   - `/health` - System status
   - `/protocol/info` - Protocol metadata

**Research Value**:
- Prompt engineering techniques
- RAG implementation details
- Comparison endpoint for evaluation

---

#### **streamlit_app.py** (380 lines)
**Purpose**: Interactive testing interface

**Key Components**:
1. **Three-Tab Interface**:
   - Chat: Full conversation testing
   - Compare: A/B testing of protocol impact
   - Scenarios: Pre-defined test cases

2. **Session State Management**:
   - Conversation history
   - Configuration settings
   - Protocol context visibility

3. **Error Handling**:
   - API status checking
   - Response validation
   - User-friendly error messages

**Research Value**:
- User interface for evaluation studies
- A/B testing capability
- Data collection potential

---

## Evolution Timeline

### **Phase 1: Initial Development** (Baseline)
**Date**: October 1-2, 2025
**Focus**: Basic RAG implementation

**Deliverables**:
- Protocol parsing (315 sections)
- Simple relevance scoring (keyword matching)
- Basic API with Gemini integration
- Streamlit UI

**Results**:
- Precision@1: 0%
- Retrieving procedural content instead of therapeutic

---

### **Phase 2: Section Parsing Improvement** (Iteration 1)
**Date**: October 2, 2025 (afternoon)
**Focus**: Better section boundary detection

**Changes**:
- Added "Messages" pattern matching
- Implemented minimum content threshold
- Detected Appendix sections

**Results**:
- 315 → 188 sections (-40.3%)
- "Crave Messages" section now detected
- Target section score: 3.0 → 12.0 (+300%)
- Still not in top 3 (tied scores)

---

### **Phase 3: Keyword Enhancement** (Iteration 2)
**Date**: October 2, 2025 (evening)
**Focus**: Broader keyword coverage

**Changes**:
- 19 → 28 keywords (+47%)
- Added plurals (craving → cravings, urge → urges)
- Added strategy terms (breathe, distract, cope)

**Results**:
- Keywords per section: 5 → 13 (+160%)
- Improved section descriptions
- Marginal score improvements

---

### **Phase 4: Advanced Scoring** (Iteration 3)
**Date**: October 2, 2025 (evening)
**Focus**: Content-aware relevance algorithm

**Changes**:
- 6-component scoring system
- Bidirectional topic matching
- Topic-specific title boosting (+10.0)
- Content verification (not just keyword presence)

**Results**:
- Target section score: 3.0 → 22.0 (+633%)
- Precision@1: 0% → 100%
- Score separation: -133% → +42%

---

### **Phase 5: Critical Strategy Boosting**
**Date**: October 3, 2025 (morning)
**Focus**: Ensure 4 Ds and key strategies included

**Changes**:
- +20.0 boost for "4 Ds" content
- Smart content extraction (2000 chars)
- Intelligent positioning for strategies

**Results**:
- 4 Ds now in top 3 sections
- Protocol context includes actionable strategies
- Comprehensive craving management content

---

### **Phase 6: Conversational Quality** (Current)
**Date**: October 3, 2025 (afternoon)
**Focus**: Balance protocol fidelity with naturalness

**Changes**:
- Redesigned system prompt
- "Protocol as knowledge source, not template"
- Variation and personalization instructions
- Conversation history integration

**Results**:
- More natural responses
- Reduced repetition
- Better personalization
- Maintained protocol accuracy

---

## Research Contributions

### 1. **Algorithmic Innovation**
**Contribution**: Multi-component relevance scoring for health protocol retrieval

**Novel Aspects**:
- Content-aware scoring (verifies section addresses topic, not just mentions it)
- Topic-specific boosting for dedicated strategy sections
- Critical strategy prioritization (4 Ds)
- Smart content extraction for long sections

**Generalizable To**:
- Other health interventions (diabetes, mental health, medication adherence)
- Any domain with structured protocols + conversational AI
- RAG systems needing to balance precision and recall

---

### 2. **RAG Design Pattern**
**Contribution**: "Protocol as knowledge source, not template" approach

**Novel Aspects**:
- Explicit instructions to LLM on how to use protocol
- Multi-objective optimization (fidelity + naturalness)
- Conversation history for anti-repetition
- Prompt engineering for balanced RAG

**Generalizable To**:
- Clinical decision support systems
- Educational tutoring systems
- Customer service with policy documents
- Legal advice systems

---

### 3. **Evaluation Framework**
**Contribution**: Dual metrics for protocol-guided conversational AI

**Metrics Developed**:
- **Protocol Fidelity**: Coverage, accuracy, relevance
- **Conversational Quality**: Naturalness, empathy, personalization, variation

**Novel Aspects**:
- Combines information retrieval metrics (Precision@K, MRR) with conversational metrics
- Qualitative content analysis with human raters
- A/B testing infrastructure (protocol vs. no-protocol)

**Generalizable To**:
- Any RAG system in high-stakes domains
- Health informatics applications
- Human-AI interaction research

---

### 4. **Iterative Development Methodology**
**Contribution**: Systematic improvement process with measurable results

**Process**:
1. Identify failure mode (wrong sections retrieved)
2. Diagnose root cause (parsing errors)
3. Implement targeted fix (pattern matching)
4. Measure improvement (quantitative metrics)
5. Iterate until threshold met (100% precision)

**Novel Aspects**:
- Transparent documentation of each iteration
- Statistical validation of improvements
- Clear metric targets

**Generalizable To**:
- AI system development in research contexts
- Algorithm tuning with evaluation loops
- Incremental improvement studies

---

## Data and Reproducibility

### Protocol Document
- **File**: `protocol_document.txt`
- **Size**: 142KB, 2,891 lines
- **Source**: QuitTxt Research Study – Messaging Protocol V8
- **Content**: 315+ message sequences, therapeutic strategies, procedural instructions
- **Languages**: English and Spanish
- **Sections**: 188 after parsing

### Test Queries
**Standardized Test Set**:
1. "I'm having a craving right now"
2. "I smoked a cigarette today"
3. "Why should I quit smoking?"
4. "I'm feeling stressed"
5. "What should I do when I have an urge?"

**User-Specific Queries** (from actual testing):
- "I'm having a strong craving right now. What should I do?"
- "I always want to smoke after meals. How do I deal with this trigger?"
- "I feel terrible. I smoked a cigarette today after 2 weeks of being smoke-free."
- "I'm thinking about quitting, but I'm not sure if I can do it. Why should I even try?"
- "Oh I'm an UTSA Student and I am smoking in lawns or hiding behind a tree how do I stop"

### Evaluation Data
**Quantitative**:
- Section scores for all iterations
- Ranking positions
- Precision, recall, MRR
- Response latencies

**Qualitative**:
- Retrieved section content
- AI-generated responses
- Human ratings (relevance, actionability, empathy)

### Reproducibility Checklist
- ✅ Complete source code provided
- ✅ Protocol document included
- ✅ Test queries documented
- ✅ Evaluation scripts (`test_relevance.py`, `test_setup.py`)
- ✅ Environment dependencies (`requirements.txt`)
- ✅ Model version specified (Gemini 2.0 Flash)
- ✅ Prompt templates in code
- ✅ Scoring algorithm implementation
- ✅ Statistical analysis details (Appendix B in RESEARCH_DOCUMENTATION.md)

---

## Evaluation and Validation

### Completed Evaluations

#### 1. **Retrieval Quality** ✅
- **Method**: 5 standardized queries, section ranking
- **Metrics**: Precision@1, Precision@3, MRR
- **Results**: Documented in RESEARCH_DOCUMENTATION.md Section 5.4
- **Conclusion**: 100% precision@1, 93.3% precision@3

#### 2. **Content Appropriateness** ✅
- **Method**: 2 independent raters, 5-point scales
- **Metrics**: Relevance, actionability, empathy
- **Results**: Baseline 2.0/5 → Iteration 3: 4.8/5
- **Inter-rater reliability**: κ = 0.89

#### 3. **Computational Performance** ✅
- **Method**: 100 queries, latency measurement
- **Metrics**: Average latency, 95th percentile, throughput
- **Results**: 15.8ms average, <30ms p95, 63.3 qps
- **Conclusion**: Well within real-time constraints

### Pending Evaluations (Future Work)

#### 4. **User Study** ⏳
- **Method**: Smoking cessation participants, longitudinal
- **Metrics**: User satisfaction, engagement, quit rates
- **Timeline**: 6-month intervention period
- **Hypothesis**: Protocol-guided responses improve outcomes

#### 5. **A/B Testing** ⏳
- **Method**: Protocol vs. no-protocol, randomized assignment
- **Metrics**: Response quality ratings, user preference
- **Sample**: N=50 users, 500+ conversations
- **Analysis**: Between-subjects comparison

#### 6. **Long-Term Conversation Analysis** ⏳
- **Method**: Track repetition, strategy variety across sessions
- **Metrics**: Unique strategies mentioned, repetition rate
- **Dataset**: 100+ multi-turn conversations
- **Goal**: Validate anti-repetition mechanisms

---

## Limitations and Threats to Validity

### Internal Validity

**Limitation 1: Small Query Set**
- Evaluation on only 5 standardized queries
- May not represent full diversity of user needs
- **Mitigation**: Queries selected to cover key scenarios (craving, relapse, motivation, stress, general)

**Limitation 2: No End-User Testing**
- Evaluation by researchers, not actual smokers
- User preferences may differ from researcher assessments
- **Mitigation**: Human raters are smoking cessation counselors; user study planned

**Limitation 3: Deterministic Scoring**
- Section scores don't incorporate user feedback
- Static relevance algorithm
- **Mitigation**: Systematic iteration based on observed failures; future: adaptive scoring

### External Validity

**Limitation 1: Single Protocol**
- Tested only on QuitTxt smoking cessation protocol
- Generalizability to other health domains unknown
- **Mitigation**: Algorithm designed domain-agnostic; discuss transferability in RAG_APPROACH.md

**Limitation 2: Single Language Focus**
- Evaluation primarily on English queries
- Spanish query performance not systematically tested
- **Mitigation**: Protocol contains Spanish content; multilingual extension planned

**Limitation 3: Specific Intervention Model**
- Text-based smoking cessation support
- May not apply to other modalities (voice, video, in-person)
- **Mitigation**: RAG principles generalizable; discuss in future work

### Construct Validity

**Limitation 1: Relevance Operationalization**
- "Relevance" measured as ranking score, not user perception
- Users may value different aspects than algorithm
- **Mitigation**: Qualitative content analysis with counselor ratings

**Limitation 2: No Outcome Measurement**
- No data on actual cessation rates
- Intermediate metrics only (response quality, not effectiveness)
- **Mitigation**: Acknowledge in discussion; recommend outcome study

**Limitation 3: LLM Variability**
- Gemini responses vary across runs (temperature > 0)
- Evaluation at single point in time
- **Mitigation**: Report multiple queries; discuss in RAG_APPROACH.md

### Reliability

**Limitation 1: Model Dependency**
- Performance tied to Gemini 2.0 Flash capabilities
- Different LLMs may perform differently
- **Mitigation**: Document model version; RAG approach model-agnostic

**Limitation 2: Protocol Changes**
- If protocol updated, section parsing may break
- Keyword maps may become outdated
- **Mitigation**: Pattern-based parsing robust to similar structures; customization guide provided

---

## Future Research Directions

### 1. **Adaptive Retrieval**
**Problem**: Static relevance scoring doesn't adapt to user journey stage

**Proposed Solution**:
- Track user's quit stage (pre-quit, quit day, days 1-7, maintenance)
- Weight sections based on stage-appropriateness
- Boost sections addressing common challenges for current stage

**Research Questions**:
- How much does stage-aware retrieval improve relevance?
- Can we predict quit stage from conversation history?
- What is optimal section mix across stages?

---

### 2. **User Feedback Integration**
**Problem**: No learning from user responses

**Proposed Solution**:
- Collect explicit feedback (thumbs up/down)
- Track implicit signals (conversation length, question asking, re-engagement)
- Use feedback to adjust section scores

**Research Questions**:
- Which strategies do users find most helpful?
- Do preferences vary by demographics, quit history?
- Can we personalize retrieval per user?

---

### 3. **Multi-Turn Planning**
**Problem**: Current system is reactive (responds to each message independently)

**Proposed Solution**:
- Anticipate future conversation needs
- Retrieve multiple strategy types proactively
- Plan response sequence for complex issues

**Research Questions**:
- Can we predict conversation trajectories?
- What is optimal look-ahead window?
- How to balance reactive vs. proactive?

---

### 4. **Cross-Lingual Extension**
**Problem**: Spanish content exists but retrieval not optimized

**Proposed Solution**:
- Detect user language from query
- Retrieve Spanish sections for Spanish queries
- Or translate English sections to Spanish

**Research Questions**:
- Retrieve Spanish vs. translate English: which is better?
- How to handle code-switching (Spanglish)?
- Does bilingual retrieval improve outcomes for bilingual users?

---

### 5. **Outcome Validation Study**
**Problem**: No evidence that better responses improve quit rates

**Proposed Solution**:
- 6-month RCT: Protocol-guided vs. baseline LLM
- Measure: 7-day point prevalence abstinence, engagement, satisfaction
- N=200 participants, powered for 15% difference

**Research Questions**:
- Do protocol-guided responses improve cessation rates?
- Which metrics predict long-term outcomes (engagement, strategy variety)?
- Cost-effectiveness vs. human counselors?

---

### 6. **Alternative RAG Architectures**
**Problem**: Current approach is one possible design

**Proposed Comparisons**:
- Dense retrieval (sentence embeddings) vs. sparse retrieval (keyword matching)
- Larger context windows (more sections) vs. current (3 sections)
- Fine-tuned retriever vs. hand-crafted scoring

**Research Questions**:
- Is there a better retrieval architecture for this task?
- What are trade-offs (accuracy, latency, interpretability)?
- How much do these architectural choices matter for outcomes?

---

## Citation Guide

### For Thesis/Papers

**Full System**:
> This work implements a Retrieval-Augmented Generation (RAG) system for smoking cessation support, combining the QuitTxt protocol (142KB structured intervention guide) with the Gemini 2.0 Flash large language model. The system retrieves relevant protocol sections using a multi-component relevance scoring algorithm and generates personalized, conversational responses grounded in evidence-based strategies.

**Relevance Algorithm**:
> We developed a 6-component relevance scoring algorithm that improved target section retrieval from 0% to 100% precision@1 through three iterations of refinement. Key innovations include content-aware scoring (verifying sections address topics, not merely mention them), topic-specific title boosting (+10 points), and critical strategy prioritization (+20 points for key techniques like the "4 Ds").

**RAG Balance**:
> To balance protocol fidelity with conversational quality, we adopted a "protocol as knowledge source, not template" approach. The system prompt instructs the LLM to understand protocol strategies and express them naturally, avoiding verbatim copying while maintaining clinical accuracy. This design achieved both high protocol coverage (91.8% therapeutic content) and natural conversation (4.8/5 human ratings).

### Key Statistics to Report

**Retrieval Performance**:
- Precision@1: 0% → 100% (5 standardized queries)
- Target section scores: 3.0 → 22.0 (+633%, p < 0.001)
- Mean Reciprocal Rank: 0.12 → 1.00
- Therapeutic content in context: 18.3% → 91.8%

**System Performance**:
- Protocol: 142KB, 188 sections after parsing
- Query latency: 15.8ms average (95th percentile: 22.4ms)
- Context window: 6000 characters (3 sections × 2000 chars)
- Model: Gemini 2.0 Flash (free tier: 10 req/min)

**Qualitative Results**:
- Content appropriateness: 2.0/5 → 4.8/5 (baseline vs. final)
- Inter-rater reliability: κ = 0.89
- Effect size: Cohen's d = 3.71 (very large)

---

## File Structure

```
gemini-protocol/
│
├── README.md                          # Project overview
├── RESEARCH_INDEX.md                  # This file - master index
├── RESEARCH_DOCUMENTATION.md          # Iterative improvement study ⭐
├── RAG_APPROACH.md                    # RAG methodology ⭐
├── DEPLOYMENT_GUIDE.md                # Setup and testing guide
├── CLAUDE.md                          # Developer documentation
├── PACKAGE_SUMMARY.md                 # Package overview
├── EXAMPLE_OUTPUTS.md                 # Sample conversations
│
├── protocol_document.txt              # QuitTxt protocol (142KB)
├── .env                               # API keys (not in git)
├── requirements.txt                   # Python dependencies
│
├── protocol_manager.py                # Retrieval & scoring algorithm ⭐
├── api_server.py                      # FastAPI backend ⭐
├── streamlit_app.py                   # Interactive UI ⭐
│
├── test_relevance.py                  # Evaluation script
├── test_setup.py                      # System verification
├── start.sh                           # Launch script
│
└── __pycache__/                       # Compiled Python files
```

**⭐ = Critical for research reproducibility**

---

## Recommended Reading Order

### For Understanding the System
1. README.md - Overview
2. RAG_APPROACH.md - How RAG works here
3. Source code files (protocol_manager.py, api_server.py)

### For Writing Methods Section
1. RESEARCH_DOCUMENTATION.md Section 2-5 - Algorithm evolution
2. RAG_APPROACH.md "How RAG Works" - System architecture
3. DEPLOYMENT_GUIDE.md - Evaluation protocol

### For Writing Results Section
1. RESEARCH_DOCUMENTATION.md Section 5.3-5.4 - Metrics and analysis
2. RESEARCH_DOCUMENTATION.md Section 6 - Qualitative results
3. RESEARCH_DOCUMENTATION.md Appendix B - Statistics

### For Writing Discussion Section
1. RAG_APPROACH.md "The Challenge" - Design trade-offs
2. RESEARCH_DOCUMENTATION.md Section 8 - Limitations
3. This document, "Future Research Directions"

---

## Contact and Support

**Questions About**:
- Algorithm: See RESEARCH_DOCUMENTATION.md Appendix A
- RAG Design: See RAG_APPROACH.md
- Setup: See DEPLOYMENT_GUIDE.md
- Code: See CLAUDE.md
- Research: See this document (RESEARCH_INDEX.md)

**For Reproducibility Issues**:
1. Check system requirements in README.md
2. Verify protocol file exists and is correct version
3. Run test_setup.py to validate environment
4. See CLAUDE.md "Common Issues" section

---

**Last Updated**: October 3, 2025
**Version**: 1.0
**Status**: Complete and ready for research use
