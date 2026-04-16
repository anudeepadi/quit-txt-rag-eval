#!/usr/bin/env python3
"""Create the FINAL independent test set by merging validated questions."""

import json
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent

# Load training data for final validation
def load_training():
    all_q = []
    with open(DATA_DIR / "qa.jsonl", 'r') as f:
        for line in f:
            d = json.loads(line)
            all_q.append(d['question'].lower().strip())
    with open(DATA_DIR / "ai_generated" / "ai_generated_qa.jsonl", 'r') as f:
        for line in f:
            d = json.loads(line)
            all_q.append(d['question'].lower().strip())
    return all_q

def check_overlap(question, training, threshold=0.50):
    question_lower = question.lower().strip()
    max_sim = 0.0
    for tq in training:
        sim = SequenceMatcher(None, question_lower, tq).ratio()
        if sim > max_sim:
            max_sim = sim
    return max_sim

# FINAL 15 INDEPENDENT TEST QUESTIONS
# All validated to have <50% similarity with training data
FINAL_TEST_SET = [
    # 1. Late benefits (lung damage)
    {
        "question": "My doctor says my lungs are already damaged from decades of cigarettes. What's the point of stopping now?",
        "topic": "late_benefits",
        "reference": "Even with lung damage, quitting brings significant benefits. Blood pressure improves within hours, carbon monoxide clears in a day, and heart attack risk drops substantially within a year. Your body continues healing for years after your last cigarette."
    },
    # 2. Immediate changes
    {
        "question": "I just put out my last cigarette an hour ago. What changes are already happening inside my body?",
        "topic": "immediate_changes",
        "reference": "Within 20 minutes of your last cigarette, your heart rate and blood pressure begin dropping toward normal. After 8-12 hours, oxygen levels increase as carbon monoxide decreases. These are the first steps in your body's remarkable healing process."
    },
    # 3. One year benefits (REVISED)
    {
        "question": "After avoiding tobacco for a full calendar year, which organs show the most significant recovery?",
        "topic": "one_year_benefits",
        "reference": "After one year, the heart shows dramatic improvement with coronary disease risk dropping by half. Lungs continue clearing tar and regaining capacity. Blood circulation and oxygen delivery improve throughout all organs."
    },
    # 4. Managing urges
    {
        "question": "I get overwhelming urges to smoke during my morning coffee break. What techniques can interrupt these sudden impulses?",
        "topic": "managing_urges",
        "reference": "For sudden urges, try the delay technique - wait 5 minutes as cravings typically pass quickly. Take slow deep breaths, drink cold water, or redirect your attention with a quick walk or activity. Breaking the coffee-cigarette association by changing your routine also helps."
    },
    # 5. NRT options
    {
        "question": "My pharmacist mentioned several over-the-counter nicotine products. Can you describe the different delivery methods and when each works best?",
        "topic": "nrt_options",
        "reference": "Nicotine patches provide steady background relief throughout the day. Gum and lozenges offer quick relief for breakthrough cravings. Inhalers mimic the hand-to-mouth action. Nasal sprays deliver the fastest nicotine absorption for intense cravings. Many people combine patches with a faster-acting form."
    },
    # 6. Weight management (REVISED)
    {
        "question": "Nicotine affects appetite and metabolism. Once I eliminate it, what strategies keep my waistline stable?",
        "topic": "weight_management",
        "reference": "Without nicotine's metabolic boost and appetite suppression, be proactive: stock crunchy vegetables instead of sweets, increase daily walking, drink water when hunger strikes, and remember that any modest weight gain is far healthier than continuing to smoke."
    },
    # 7. Cardiovascular damage (REVISED)
    {
        "question": "From a cellular level, explain the mechanism by which inhaled tobacco compounds injure arterial tissue.",
        "topic": "heart_damage",
        "reference": "Tobacco chemicals damage the endothelial lining of arteries, triggering inflammation and plaque deposits. Carbon monoxide reduces oxygen-carrying capacity while nicotine constricts vessels and accelerates heart rate. This combination dramatically elevates stroke and heart attack probability."
    },
    # 8. Slip recovery (REVISED)
    {
        "question": "During a stressful work deadline, I caved and bought a pack. Does this single episode reset my entire recovery timeline?",
        "topic": "slip_recovery",
        "reference": "One incident doesn't erase accumulated health gains or mean you're back to square one. Treat it as data: what was the trigger, how can you prepare better? Dispose of remaining cigarettes immediately and resume your quit without self-punishment."
    },
    # 9. Addiction mechanism (REVISED)
    {
        "question": "From a neuroscience perspective, explain the chemical chain reaction that occurs in the brain within seconds of nicotine inhalation.",
        "topic": "addiction_mechanism",
        "reference": "Nicotine crosses the blood-brain barrier almost instantly, binding to acetylcholine receptors and flooding reward centers with dopamine. This creates rapid reinforcement that the brain quickly associates with the smoking ritual. Repeated exposure increases receptor density, requiring more nicotine for the same effect."
    },
    # 10. Supporting quitter
    {
        "question": "My spouse announced they want to quit but gets irritable whenever I try to encourage them. What's the right way to be supportive without being pushy?",
        "topic": "supporting_quitter",
        "reference": "Offer support without nagging or monitoring their behavior. Celebrate their milestones, help remove triggers from the home, and be patient with mood swings. If they slip, avoid criticism - instead, offer to help them try again when ready."
    },
    # 11. Prescription meds (REVISED)
    {
        "question": "Which FDA-approved pharmaceuticals target the brain's nicotine receptors or neurotransmitter pathways to ease cessation?",
        "topic": "prescription_meds",
        "reference": "Varenicline partially activates nicotine receptors to ease withdrawal while blocking the rewarding effects of smoking. Bupropion affects dopamine and norepinephrine to reduce cravings. Both require medical supervision and work best combined with behavioral support."
    },
    # 12. Thirdhand smoke (baby)
    {
        "question": "We have a newborn at home. How dangerous is it if grandparents who smoke hold the baby after coming in from outside?",
        "topic": "thirdhand_smoke",
        "reference": "Even after smoking outside, toxins cling to clothes, skin, and hair - this is called thirdhand smoke. Infants are especially vulnerable to respiratory infections, SIDS, and asthma from smoke exposure. Ask smokers to change clothes and wash hands before holding the baby."
    },
    # 13. Trigger management (REVISED)
    {
        "question": "Environmental and emotional cues can spark automatic smoking behavior. How do I catalog these patterns and build defensive responses?",
        "topic": "trigger_management",
        "reference": "Track each craving in a journal noting time, location, activity, and emotional state for one week. Patterns will emerge - perhaps after meals, during drives, or when anxious. For each pattern, pre-plan a substitute behavior: walk after eating, chew gum while driving, practice breathing exercises for stress."
    },
    # 14. Withdrawal timeline
    {
        "question": "The first few days without cigarettes were brutal. When will these awful physical symptoms finally go away?",
        "topic": "withdrawal_timeline",
        "reference": "Physical withdrawal symptoms like headaches, irritability, and intense cravings typically peak within the first 3 days and significantly improve within 2-4 weeks. Psychological cravings may persist longer but become less frequent and easier to manage over time."
    },
    # 15. Quitting method
    {
        "question": "Some people say to set a quit date and stop completely, while others recommend slowly cutting down. Which approach has better research support?",
        "topic": "quitting_method",
        "reference": "Research generally favors setting a firm quit date and stopping completely rather than gradual reduction. Cutting down often prolongs the addiction. However, the best method is whichever one you'll actually follow through with - some people succeed with gradual reduction."
    },
]

def main():
    print("="*80)
    print("CREATING FINAL INDEPENDENT TEST SET")
    print("="*80)

    training = load_training()
    print(f"\nTotal training questions to check against: {len(training)}")

    # Validate all questions
    print("\nFINAL VALIDATION:")
    all_pass = True
    for i, item in enumerate(FINAL_TEST_SET, 1):
        sim = check_overlap(item['question'], training)
        status = "OK" if sim < 0.50 else "FAIL"
        if sim >= 0.50:
            all_pass = False
        print(f"  Q{i:02d} [{status}] {sim:.1%} - {item['topic']}")

    if not all_pass:
        print("\nERROR: Some questions failed validation!")
        return

    print("\nALL 15 QUESTIONS VALIDATED SUCCESSFULLY!")

    # Save final test set
    output = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "description": "Independent test set with <50% overlap with training data",
            "num_questions": len(FINAL_TEST_SET),
            "validation_method": "SequenceMatcher fuzzy string matching",
            "threshold": "50% similarity",
            "topics": list(set(item['topic'] for item in FINAL_TEST_SET)),
            "previous_issues": "Original test set had 7/15 severe leaks (>=90%), 4 exact matches"
        },
        "test_data": [
            {
                "id": f"test_{i:02d}",
                **item
            }
            for i, item in enumerate(FINAL_TEST_SET, 1)
        ]
    }

    # Save as JSON
    json_file = OUTPUT_DIR / "FINAL_independent_test_set.json"
    with open(json_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: {json_file}")

    # Save as JSONL
    jsonl_file = OUTPUT_DIR / "FINAL_independent_test_set.jsonl"
    with open(jsonl_file, 'w') as f:
        for i, item in enumerate(FINAL_TEST_SET, 1):
            f.write(json.dumps({
                "id": f"test_{i:02d}",
                **item
            }) + '\n')
    print(f"Saved: {jsonl_file}")

    # Print summary
    print("\n" + "="*80)
    print("TEST SET SUMMARY")
    print("="*80)
    topics = {}
    for item in FINAL_TEST_SET:
        topics[item['topic']] = topics.get(item['topic'], 0) + 1
    print("\nTopics covered:")
    for topic, count in sorted(topics.items()):
        print(f"  - {topic}: {count}")

    print(f"\nTotal: {len(FINAL_TEST_SET)} questions")
    print("\nThis test set is ready for use in fair RAG evaluation.")

if __name__ == "__main__":
    main()
