#!/usr/bin/env python3
"""Create an independent test set with ZERO overlap with training data.

This script:
1. Proposes new test questions covering key topics
2. Validates they don't overlap with training data
3. Generates reference answers
4. Outputs a validated test set
"""

import json
import os
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Tuple

# Load environment for OpenAI
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

from openai import OpenAI

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_training_questions() -> Tuple[List[str], List[str]]:
    """Load all questions from both training datasets."""
    human_questions = []
    with open(DATA_DIR / "qa.jsonl", 'r') as f:
        for line in f:
            d = json.loads(line)
            human_questions.append(d['question'].lower().strip())

    ai_questions = []
    with open(DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl", 'r') as f:
        for line in f:
            d = json.loads(line)
            ai_questions.append(d['question'].lower().strip())

    return human_questions, ai_questions

def check_overlap(question: str, training_questions: List[str], threshold: float = 0.5) -> Tuple[bool, float, str]:
    """Check if a question overlaps with training data.

    Returns: (is_clean, max_similarity, best_match)
    """
    question_lower = question.lower().strip()
    max_sim = 0.0
    best_match = ""

    for tq in training_questions:
        sim = SequenceMatcher(None, question_lower, tq).ratio()
        if sim > max_sim:
            max_sim = sim
            best_match = tq

    return max_sim < threshold, max_sim, best_match

# New candidate test questions - designed to be semantically different
# while covering the same topics
CANDIDATE_QUESTIONS = [
    # Benefits/Timeline (replaces Q1, Q2, Q9)
    {
        "question": "My doctor says my lungs are already damaged from decades of cigarettes. What's the point of stopping now?",
        "topic": "late_benefits",
        "reference": "Even with lung damage, quitting brings significant benefits. Blood pressure improves within hours, carbon monoxide clears in a day, and heart attack risk drops substantially within a year. Your body continues healing for years after your last cigarette."
    },
    {
        "question": "I just put out my last cigarette an hour ago. What changes are already happening inside my body?",
        "topic": "immediate_changes",
        "reference": "Within 20 minutes of your last cigarette, your heart rate and blood pressure begin dropping toward normal. After 8-12 hours, oxygen levels increase as carbon monoxide decreases. These are the first steps in your body's remarkable healing process."
    },
    {
        "question": "If I manage to stay smoke-free for twelve months, what health improvements should I expect to see?",
        "topic": "one_year_benefits",
        "reference": "After one year without smoking, your risk of coronary heart disease drops to about half that of a current smoker. Lung function continues improving, circulation gets better, and your body's overall cardiovascular health shows marked improvement."
    },

    # Cravings/Urges (replaces Q3)
    {
        "question": "I get overwhelming urges to smoke during my morning coffee break. What techniques can interrupt these sudden impulses?",
        "topic": "managing_urges",
        "reference": "For sudden urges, try the delay technique - wait 5 minutes as cravings typically pass quickly. Take slow deep breaths, drink cold water, or redirect your attention with a quick walk or activity. Breaking the coffee-cigarette association by changing your routine also helps."
    },

    # NRT (replaces Q4)
    {
        "question": "My pharmacist mentioned several over-the-counter nicotine products. Can you describe the different delivery methods and when each works best?",
        "topic": "nrt_options",
        "reference": "Nicotine patches provide steady background relief throughout the day. Gum and lozenges offer quick relief for breakthrough cravings. Inhalers mimic the hand-to-mouth action. Nasal sprays deliver the fastest nicotine absorption for intense cravings. Many people combine patches with a faster-acting form."
    },

    # Weight (replaces Q5 - EXACT MATCH)
    {
        "question": "Several of my friends packed on pounds after they stopped smoking. How can I prevent this from happening to me?",
        "topic": "weight_management",
        "reference": "Weight gain occurs because nicotine suppresses appetite and boosts metabolism. Combat this by planning healthy snacks like carrots or sugar-free gum, increasing physical activity, and drinking plenty of water. The average gain of 5-10 pounds is far less harmful than continued smoking."
    },

    # Cardiovascular (replaces Q6 - EXACT MATCH)
    {
        "question": "My cardiologist is concerned about my arteries. In what specific ways does tobacco smoke damage the heart and blood vessels?",
        "topic": "heart_damage",
        "reference": "Tobacco smoke damages artery walls, promotes plaque buildup, raises blood pressure, and reduces blood oxygen while increasing carbon monoxide. It makes blood stickier and more prone to clotting, significantly elevating heart attack and stroke risk."
    },

    # Relapse (replaces Q7 - EXACT MATCH)
    {
        "question": "Last night at a party I smoked three cigarettes after being quit for two months. Have I completely destroyed my progress?",
        "topic": "slip_recovery",
        "reference": "A slip doesn't erase your progress or mean you've failed. Most successful quitters have multiple attempts. Analyze what triggered the slip, recommit immediately, and don't let shame spiral into resuming regular smoking. Your two months of healing aren't wasted."
    },

    # Addiction mechanism (replaces Q8 - already clean, keep similar)
    {
        "question": "What makes cigarettes so incredibly difficult to give up compared to other habits?",
        "topic": "addiction_mechanism",
        "reference": "Nicotine hijacks your brain's reward system, triggering dopamine release within seconds of inhaling. Over time, your brain adapts by creating more nicotine receptors and reducing natural dopamine. Withdrawal then creates intense physical and psychological discomfort that only nicotine relieves."
    },

    # Supporting others (replaces Q10)
    {
        "question": "My spouse announced they want to quit but gets irritable whenever I try to encourage them. What's the right way to be supportive without being pushy?",
        "topic": "supporting_quitter",
        "reference": "Offer support without nagging or monitoring their behavior. Celebrate their milestones, help remove triggers from the home, and be patient with mood swings. If they slip, avoid criticism - instead, offer to help them try again when ready."
    },

    # Medications (replaces Q11)
    {
        "question": "Beyond nicotine replacement, what prescription medications exist that can reduce the urge to smoke?",
        "topic": "prescription_meds",
        "reference": "Varenicline (Chantix) blocks nicotine receptors and reduces the pleasure from smoking while easing withdrawal. Bupropion (Zyban/Wellbutrin) is an antidepressant that reduces cravings and withdrawal symptoms. Both require a doctor's prescription and work best as part of a comprehensive plan."
    },

    # Secondhand smoke (replaces Q12 - EXACT MATCH)
    {
        "question": "We have a newborn at home. How dangerous is it if grandparents who smoke hold the baby after coming in from outside?",
        "topic": "thirdhand_smoke",
        "reference": "Even after smoking outside, toxins cling to clothes, skin, and hair - this is called thirdhand smoke. Infants are especially vulnerable to respiratory infections, SIDS, and asthma from smoke exposure. Ask smokers to change clothes and wash hands before holding the baby."
    },

    # Triggers (replaces Q13)
    {
        "question": "Certain situations make me crave a cigarette badly. How do I identify my personal smoking triggers and create strategies around them?",
        "topic": "trigger_management",
        "reference": "Common triggers include stress, alcohol, coffee, driving, and social situations with smokers. Keep a trigger journal for a week before quitting. For each trigger, plan an alternative - change routines, avoid bars initially, drink tea instead of coffee, and ask smoking friends to support your quit."
    },

    # Withdrawal duration (replaces Q14)
    {
        "question": "The first few days without cigarettes were brutal. When will these awful physical symptoms finally go away?",
        "topic": "withdrawal_timeline",
        "reference": "Physical withdrawal symptoms like headaches, irritability, and intense cravings typically peak within the first 3 days and significantly improve within 2-4 weeks. Psychological cravings may persist longer but become less frequent and easier to manage over time."
    },

    # Quitting method (replaces Q15 - already clean, keep similar)
    {
        "question": "Some people say to set a quit date and stop completely, while others recommend slowly cutting down. Which approach has better research support?",
        "topic": "quitting_method",
        "reference": "Research generally favors setting a firm quit date and stopping completely rather than gradual reduction. Cutting down often prolongs the addiction. However, the best method is whichever one you'll actually follow through with - some people succeed with gradual reduction."
    },
]

def main():
    print("="*80)
    print("CREATING INDEPENDENT TEST SET")
    print("="*80)

    # Load training data
    print("\nLoading training datasets...")
    human_q, ai_q = load_training_questions()
    all_training = human_q + ai_q
    print(f"  Human-curated: {len(human_q)} questions")
    print(f"  AI-generated: {len(ai_q)} questions")
    print(f"  Total to check against: {len(all_training)} questions")

    # Validate each candidate
    print("\n" + "="*80)
    print("VALIDATING CANDIDATE QUESTIONS")
    print("="*80)

    validated = []
    rejected = []

    for i, candidate in enumerate(CANDIDATE_QUESTIONS, 1):
        q = candidate['question']
        is_clean, max_sim, best_match = check_overlap(q, all_training, threshold=0.50)

        status = "PASS" if is_clean else "FAIL"
        print(f"\n[{status}] Q{i}: {q[:60]}...")
        print(f"       Max similarity: {max_sim:.1%}")
        if max_sim > 0.3:
            print(f"       Closest match: '{best_match[:50]}...'")

        if is_clean:
            validated.append({
                "id": f"test_{i:02d}",
                "question": q,
                "topic": candidate['topic'],
                "reference": candidate['reference'],
                "max_training_similarity": round(max_sim, 3)
            })
        else:
            rejected.append({
                "question": q,
                "similarity": max_sim,
                "match": best_match
            })

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  Validated: {len(validated)}/{len(CANDIDATE_QUESTIONS)}")
    print(f"  Rejected: {len(rejected)}/{len(CANDIDATE_QUESTIONS)}")

    if rejected:
        print("\n  REJECTED QUESTIONS (need rewriting):")
        for r in rejected:
            print(f"    - {r['similarity']:.1%}: '{r['question'][:50]}...'")

    # Save validated test set
    output_file = Path(__file__).parent / "independent_test_set.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metadata": {
                "created": "2026-01-10",
                "method": "Fuzzy match validation with 50% similarity threshold",
                "num_questions": len(validated),
                "topics_covered": list(set(v['topic'] for v in validated))
            },
            "test_data": validated
        }, f, indent=2)

    print(f"\n  Saved to: {output_file}")

    # Also save as JSONL for easy loading
    jsonl_file = Path(__file__).parent / "independent_test_set.jsonl"
    with open(jsonl_file, 'w') as f:
        for item in validated:
            f.write(json.dumps(item) + '\n')
    print(f"  Also saved as: {jsonl_file}")

    return validated

if __name__ == "__main__":
    main()
