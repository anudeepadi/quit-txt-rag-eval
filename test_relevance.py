#!/usr/bin/env python3
"""
Test script to verify protocol relevance scoring improvements
"""
from protocol_manager import ProtocolContextManager

def test_relevance_scoring():
    """Test the improved relevance scoring"""
    print("=" * 70)
    print("Testing Protocol Relevance Scoring")
    print("=" * 70)

    # Initialize manager
    manager = ProtocolContextManager('protocol_document.txt')
    print(f"\n✅ Loaded protocol with {len(manager.sections)} sections\n")

    # Test messages
    test_messages = [
        "I'm having a craving right now",
        "I smoked a cigarette today",
        "Why should I quit smoking?",
        "I'm feeling stressed",
        "What should I do when I have an urge?",
    ]

    for message in test_messages:
        print(f"\n{'='*70}")
        print(f"Message: '{message}'")
        print(f"{'='*70}")

        # Get debug info
        top_sections = manager.debug_relevance(message, top_n=5)

        print(f"\nTop 5 Relevant Sections:")
        for i, (title, score, keywords) in enumerate(top_sections, 1):
            print(f"\n{i}. Score: {score:.1f}")
            print(f"   Title: {title[:80]}")
            print(f"   Keywords: {', '.join(keywords[:5])}")

        # Get actual context that would be used
        print(f"\n{'─'*70}")
        print("Context that would be sent to AI:")
        print(f"{'─'*70}")
        context = manager.get_relevant_context(message, max_sections=3)

        # Show just the section titles
        lines = context.split('\n')
        for line in lines:
            if line.startswith('## '):
                print(f"  • {line[3:]}")

    print(f"\n{'='*70}")
    print("✅ Testing complete!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_relevance_scoring()
