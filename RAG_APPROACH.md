# Retrieval-Augmented Generation (RAG) Approach in QuitTxt

## Overview

This system uses **Retrieval-Augmented Generation (RAG)**, also called in-context learning, to combine the benefits of:
1. **Large Language Models (LLMs)**: Natural, conversational, empathetic responses
2. **Structured Protocol**: Evidence-based smoking cessation strategies validated by research

## How RAG Works Here

### 1. **Retrieval Phase**
```
User Message → Relevance Scoring → Top 3 Protocol Sections → Context
```

When a user sends a message like "I'm having a craving":
- System scores all 188 protocol sections for relevance
- Selects top 3 most relevant sections (e.g., "Crave Messages", sections with "4 Ds")
- Extracts up to 2000 characters from each section

### 2. **Augmentation Phase**
```
System Prompt + Protocol Context + Conversation History + User Message → Full Prompt
```

The complete prompt sent to Gemini includes:
- **System instructions**: How to use the protocol
- **Protocol sections**: Evidence-based strategies
- **Conversation history**: Last 5 messages for personalization
- **Current message**: User's current need

### 3. **Generation Phase**
```
Full Prompt → Gemini 2.0 Flash → Personalized Response
```

The LLM generates a response that:
- Is grounded in protocol strategies
- Uses natural, conversational language
- Adapts to the user's specific situation
- Avoids verbatim copying of protocol text

## The Challenge: Protocol Fidelity vs. Conversational Quality

### The Tension

There's an inherent trade-off in RAG systems:

| Aspect | Too Much Protocol Fidelity | Too Much LLM Freedom |
|--------|---------------------------|---------------------|
| **Pros** | Evidence-based, clinically validated | Natural, engaging, personalized |
| **Cons** | Robotic, repetitive, templated | May give incorrect advice, miss key strategies |
| **Example** | "Think of your craving like traffic" (exact protocol phrase repeated) | "Just distract yourself" (generic, misses 4 Ds technique) |

### Our Solution: Principled RAG

**Version 1 (Too Strict)**:
```
"You MUST use the exact strategies from the protocol"
→ Result: Robotic, repetitive responses copying protocol verbatim
```

**Version 2 (Balanced - Current)**:
```
"Draw from protocol strategies but express them naturally"
→ Result: Evidence-based + conversational + personalized
```

### Key Design Decisions

#### 1. **Strategy Extraction, Not Template Filling**

❌ **Bad (Template)**: "Remember the 4 Ds: Delay, Drink water, Deep breathe, Do something else"

✅ **Good (Extraction)**: "When a craving hits, try these four simple steps: First, delay acting on the urge for just 5 minutes. During that time, drink some cold water to occupy your mouth and hands. Take a few slow, deep breaths to calm your nervous system. Finally, shift your focus by doing something else - anything from a quick walk to watching a funny video. Most cravings pass within 5-10 minutes if you ride them out."

**Difference**: Both convey the 4 Ds, but the second explains WHY each works and HOW to do them.

#### 2. **Variation Across Responses**

The protocol might have 23 different craving strategies. The system should:
- Not repeat the same strategy every time
- Vary language and examples
- Adapt based on conversation history

**Example**:
- First craving query → breathing exercises
- Second craving query → distraction techniques
- Third craving query → calling a friend
- Fourth craving query → 4 Ds framework (if not mentioned before)

#### 3. **Personalization Based on Context**

**Generic response**: "Cravings are tough, but they pass."

**Personalized responses**:
- UTSA student smoking behind trees → "I understand it's hard when you're on campus and see others smoking. Try avoiding your usual smoking spots - instead of going behind that tree during breaks, head to the library or call a friend."
- After meals → "It's super common to associate smoking with finishing a meal - you've built that habit over time. Try replacing it with a new ritual, like taking a 5-minute walk or chewing gum."
- 2 weeks smoke-free → "You've made it 2 whole weeks - that's incredible! Your body is already healing. This craving is just your brain adjusting to the new normal. You've proven you can resist for 14 days; you can handle the next 5 minutes."

## Evaluation Metrics for RAG Quality

### Protocol Fidelity Metrics

1. **Strategy Coverage**: Are evidence-based strategies mentioned?
   - 4 Ds technique
   - Breathing exercises
   - Social support
   - Distraction methods

2. **Accuracy**: Are strategies explained correctly?
   - No contradictions with protocol
   - No medically incorrect advice

3. **Relevance**: Does the protocol content match the query?
   - Craving query → craving strategies (not quit date setting)

### Conversational Quality Metrics

1. **Naturalness**: Does it sound like a human counselor?
   - 5-point scale rated by human evaluators
   - Avoid robotic, templated language

2. **Empathy**: Does it acknowledge the user's feelings?
   - Recognition of difficulty/distress
   - Validation before advice

3. **Personalization**: Does it reference user's specific context?
   - Mentions previous conversation
   - Adapts to user's situation (student, after meals, relapse, etc.)

4. **Variation**: Does it avoid repetition?
   - Different strategies across similar queries
   - Different language/examples for same strategy

### Combined Metrics

**Ideal Response Characteristics**:
- ✅ Mentions at least one evidence-based strategy from protocol
- ✅ Explains HOW to use the strategy, not just names it
- ✅ Uses conversational language, not protocol verbatim
- ✅ Acknowledges user's specific situation/emotions
- ✅ Different from previous responses in conversation
- ✅ 3-5 sentences (substantive but concise)

## Technical Implementation

### System Prompt Design

**Structure**:
1. **Role Definition**: "Compassionate smoking cessation counselor"
2. **Guidelines**: 7 specific response principles
3. **Avoidance List**: What NOT to do
4. **Protocol Context**: Inserted here
5. **Usage Instructions**: How to interpret protocol

**Key Phrases**:
- "Draw from... but express them naturally"
- "Explain HOW to use them, not just THAT they exist"
- "Avoid repeating the same phrases or metaphors"
- "Reference the user's specific situation"

### Protocol Context Formatting

```
=== RELEVANT PROTOCOL SECTIONS ===

## Crave Messages
[23 different craving strategies]

## END OF MESSAGING SESSION
[Additional strategies including 4 Ds]

HOW TO USE THE PROTOCOL:
- Understand the PRINCIPLES and STRATEGIES from the sections above
- Express these strategies in natural, conversational language
- Combine protocol wisdom with empathy and personalization
```

### Conversation History Integration

```
=== CONVERSATION HISTORY ===
(Use this history to personalize your response and avoid repeating previous advice)

USER: I'm having a craving
ASSISTANT: [previous response about breathing]
USER: I'm having another craving
ASSISTANT: [should give DIFFERENT strategy, not repeat breathing]
```

## Research Questions

### Current Limitations

1. **No User Feedback Loop**: System doesn't learn which strategies users find most helpful
2. **Static Relevance Scoring**: Doesn't adapt based on conversation stage (early vs. late in quit journey)
3. **No Outcome Tracking**: Can't measure if responses actually help users quit
4. **Language Model Variability**: Gemini's responses vary; need consistency testing

### Future Work

1. **Adaptive RAG**: Adjust retrieval based on:
   - User's quit stage (pre-quit, quit day, maintenance)
   - Previously successful strategies for this user
   - Time since last cigarette

2. **Reinforcement Learning from Human Feedback (RLHF)**:
   - Collect user ratings of response quality
   - Fine-tune retrieval and generation based on feedback

3. **Multi-Turn Planning**:
   - System anticipates future conversation needs
   - Retrieves multiple strategy types to avoid running out

4. **Comparative Study**:
   - Protocol-guided responses vs. unguided LLM
   - Measure: user satisfaction, engagement, quit rates

5. **Cross-Lingual RAG**:
   - Handle Spanish queries with English protocol
   - Or retrieve Spanish protocol sections for Spanish queries

## Best Practices for Protocol-Guided RAG

### For Health Interventions

1. **Balance is Critical**: Don't sacrifice conversational quality for protocol fidelity, or vice versa
2. **Explain, Don't Dictate**: Users respond better to understanding WHY a strategy works
3. **Personalization Matters**: Generic advice feels less trustworthy
4. **Variation Prevents Burnout**: Users disengage from repetitive responses
5. **Empathy First**: Acknowledge feelings before offering solutions

### For System Design

1. **Iterate on Prompts**: Version 1 will be too strict or too loose
2. **Test with Real Conversations**: Single-turn evaluation misses repetition issues
3. **Monitor Protocol Coverage**: Ensure important strategies aren't missed
4. **Human Evaluation Essential**: Automated metrics miss nuance
5. **Conversation History Crucial**: Context prevents robotic responses

## Comparison to Other Approaches

### Alternative 1: Fine-Tuned Model
**Approach**: Fine-tune LLM on protocol-following conversations

**Pros**:
- No retrieval latency
- Can learn protocol style
- More consistent

**Cons**:
- Requires training data (conversations)
- Expensive to fine-tune
- Hard to update protocol
- May hallucinate or drift from protocol

### Alternative 2: Rule-Based System
**Approach**: If-then rules mapping queries to protocol sections

**Pros**:
- Completely controllable
- No LLM unpredictability
- Transparent

**Cons**:
- Extremely robotic
- Can't handle novel queries
- No personalization
- High maintenance

### Alternative 3: Pure LLM (No RAG)
**Approach**: Just prompt LLM with protocol once at start

**Pros**:
- Most natural responses
- Highly conversational
- Creative

**Cons**:
- Forgets protocol details
- May give incorrect advice
- No grounding in specific strategies
- Inconsistent

### Why RAG is Optimal Here

| Criterion | Rule-Based | Fine-Tuned | Pure LLM | **RAG** |
|-----------|-----------|-----------|----------|---------|
| Protocol fidelity | ✅ High | ⚠️ Medium | ❌ Low | ✅ High |
| Conversational quality | ❌ Low | ✅ High | ✅ High | ✅ High |
| Personalization | ❌ Low | ✅ High | ✅ High | ✅ High |
| Updatable protocol | ❌ Hard | ❌ Hard | ⚠️ Medium | ✅ Easy |
| Explainability | ✅ High | ❌ Low | ❌ Low | ✅ High |
| Development cost | ⚠️ Medium | ❌ High | ✅ Low | ⚠️ Medium |

**RAG Advantages**:
- ✅ Protocol sections explicitly in context (grounded, explainable)
- ✅ LLM flexibility for natural language (conversational)
- ✅ Easy to update protocol (just change text file)
- ✅ No training data required
- ✅ Can inspect exactly what protocol content was used

## Conclusion

This QuitTxt system demonstrates that **RAG can achieve both protocol fidelity and conversational quality** through careful prompt engineering. The key insight is:

> **Protocol as knowledge source, not template**

The protocol provides evidence-based strategies that the LLM should *understand* and *explain naturally*, not copy verbatim. This approach enables:
- Clinically validated advice
- Natural, empathetic conversation
- Personalization to user context
- Variation across responses

The balance is achieved through:
1. High-quality retrieval (right protocol sections)
2. Thoughtful augmentation (clear instructions on how to use protocol)
3. Guided generation (principles, not templates)

This serves as a model for other health intervention RAG systems where domain knowledge must be preserved but delivered conversationally.

---

**Last Updated**: October 2025
**Related**: RESEARCH_DOCUMENTATION.md, CLAUDE.md
