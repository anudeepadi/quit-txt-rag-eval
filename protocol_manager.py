"""
Protocol Context Manager
Intelligently extracts and manages relevant sections of the QuitTxt protocol document
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ProtocolSection:
    """Represents a section of the protocol"""
    title: str
    content: str
    keywords: List[str]
    relevance_score: float = 0.0


class ProtocolContextManager:
    """Manages protocol document and provides relevant context for queries"""
    
    def __init__(self, protocol_file: str):
        self.protocol_file = protocol_file
        self.full_protocol = self._load_protocol()
        self.sections = self._parse_sections()
        self.keyword_map = self._build_keyword_map()
        
    def _load_protocol(self) -> str:
        """Load the protocol document"""
        with open(self.protocol_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_sections(self) -> List[ProtocolSection]:
        """Parse protocol into logical sections"""
        sections = []

        # Split by major headings or logical breaks
        lines = self.full_protocol.split('\n')
        current_section = []
        current_title = "Introduction"

        for line in lines:
            stripped = line.strip()

            # Detect section headers (more specific patterns)
            is_header = False

            # Major headers: all caps with meaningful content (longer than 3 chars)
            if stripped.isupper() and len(stripped) > 3 and stripped.replace(' ', '').isalpha():
                is_header = True
            # Message type headers: specific patterns like "PQ-6Motiv1 Messaging:", "Crave Messages"
            elif any(pattern in stripped for pattern in ['Messaging:', 'Messages', 'Message:', 'INTAKE', 'Response']):
                if stripped.endswith(':') or 'Messaging' in stripped or 'Messages' in stripped:
                    is_header = True
            # Numbered sections like "Q30", "Q35"
            elif stripped.startswith('Q') and len(stripped) > 1 and stripped[1:].split()[0].isdigit():
                is_header = True
            # Appendix headers
            elif stripped.startswith('Appendix'):
                is_header = True

            if is_header and current_section:
                content = '\n'.join(current_section).strip()
                # Only create section if it has substantial content
                if len(content) > 20:
                    keywords = self._extract_keywords(content)
                    sections.append(ProtocolSection(
                        title=current_title,
                        content=content,
                        keywords=keywords
                    ))
                current_title = stripped
                current_section = []
            else:
                current_section.append(line)

        # Add last section
        if current_section:
            content = '\n'.join(current_section).strip()
            if len(content) > 20:
                keywords = self._extract_keywords(content)
                sections.append(ProtocolSection(
                    title=current_title,
                    content=content,
                    keywords=keywords
                ))

        return sections
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Common smoking cessation keywords
        keywords = set()

        smoking_terms = [
            'quit', 'smoking', 'cigarette', 'tobacco', 'nicotine',
            'craving', 'cravings', 'urge', 'urges', 'withdrawal',
            'relapse', 'slip', 'motivation', 'support',
            'trigger', 'stress', 'habit', 'health', 'goal',
            'cessation', 'abstinence', 'recovery', 'temptation',
            'breathe', 'breathing', 'distract', 'delay', 'drink water',
            '4 ds', 'exercise', 'active', 'cope', 'deal with'
        ]

        text_lower = text.lower()
        for term in smoking_terms:
            if term in text_lower:
                keywords.add(term)

        return list(keywords)
    
    def _build_keyword_map(self) -> Dict[str, List[str]]:
        """Build a map of keywords to topics"""
        return {
            'craving': ['craving', 'cravings', 'urge', 'urges', 'temptation', 'want', 'need', '4 ds', 'delay', 'distract', 'deep breathe', 'drink water'],
            'motivation': ['motivation', 'reason', 'reasons', 'why', 'goal', 'benefit', 'live longer'],
            'support': ['help', 'support', 'friend', 'family', 'group', 'talk', 'call'],
            'relapse': ['relapse', 'slip', 'slipped', 'smoke again', 'smoked', 'failed', 'mistake', 'cigarette'],
            'withdrawal': ['withdrawal', 'symptom', 'symptoms', 'irritable', 'anxious', 'mood', 'angry'],
            'stress': ['stress', 'stressed', 'anxiety', 'anxious', 'worried', 'pressure', 'tension', 'calm'],
            'health': ['health', 'healthy', 'body', 'lung', 'lungs', 'disease', 'cancer'],
            'trigger': ['trigger', 'triggers', 'situation', 'place', 'people', 'when', 'alcohol', 'drinking'],
            'strategy': ['strategy', 'strategies', 'tip', 'tips', 'technique', 'way', 'method', 'how', 'cope', 'deal with', 'exercise', 'breathing'],
            'progress': ['progress', 'improvement', 'better', 'success', 'achievement', 'doing great', 'proud', 'days']
        }
    
    def get_relevant_context(self, user_message: str, max_sections: int = 3) -> str:
        """Get relevant protocol sections for a user message"""
        # Score each section
        for section in self.sections:
            section.relevance_score = self._calculate_relevance(user_message, section)

        # Sort by relevance
        relevant_sections = sorted(
            self.sections,
            key=lambda s: s.relevance_score,
            reverse=True
        )[:max_sections]

        # Format context
        context = "=== RELEVANT PROTOCOL SECTIONS ===\n\n"
        for section in relevant_sections:
            if section.relevance_score > 0:
                context += f"## {section.title}\n"

                # For sections with critical strategies, try to include them
                content = section.content
                max_length = 2000  # Increased from 1500

                # If section is too long and contains critical strategies,
                # try to include the part with the strategies
                if len(content) > max_length:
                    # Check for critical strategy keywords
                    strategy_keywords = ['4 d', 'delay, drink', 'breathing exercise']
                    found_strategy = False

                    for keyword in strategy_keywords:
                        if keyword in content.lower():
                            # Find position of strategy
                            pos = content.lower().find(keyword)
                            if pos > max_length // 2:
                                # Strategy is in the latter half, adjust start position
                                start = max(0, pos - max_length // 2)
                                content = "..." + content[start:start + max_length]
                                found_strategy = True
                                break

                    if not found_strategy:
                        content = content[:max_length] + "..."
                else:
                    pass  # Use full content

                context += f"{content}\n\n"

        return context

    def debug_relevance(self, user_message: str, top_n: int = 5) -> List[tuple]:
        """Debug method to see top scoring sections"""
        for section in self.sections:
            section.relevance_score = self._calculate_relevance(user_message, section)

        relevant_sections = sorted(
            self.sections,
            key=lambda s: s.relevance_score,
            reverse=True
        )[:top_n]

        return [(s.title, s.relevance_score, s.keywords) for s in relevant_sections]
    
    def _calculate_relevance(self, message: str, section: ProtocolSection) -> float:
        """Calculate how relevant a section is to the user message"""
        message_lower = message.lower()
        section_content_lower = section.content.lower()
        score = 0.0

        # Extract key terms from user message
        message_words = set(message_lower.split())

        # 1. Direct keyword matches in section content (highest priority)
        for keyword in section.keywords:
            if keyword in message_lower:
                # Keyword appears in both message and section
                score += 5.0

        # 2. Check if message terms appear in section content
        for word in message_words:
            if len(word) > 3 and word in section_content_lower:
                score += 2.0

        # 3. Check keyword map topics
        for topic, terms in self.keyword_map.items():
            for term in terms:
                if term in message_lower and term in section_content_lower:
                    # Both message and section mention this topic
                    score += 3.0
                elif term in message_lower:
                    # Only message mentions it
                    score += 0.5

        # 4. Check if section title is relevant
        title_lower = section.title.lower()
        title_words = set(title_lower.split())

        # Check for exact word matches in title
        for word in message_words:
            if len(word) > 3 and word in title_words:
                score += 6.0

        # Check for partial matches in title (e.g., "crave" in "Crave Messages")
        for word in message_words:
            if len(word) > 3 and word in title_lower:
                score += 4.0

        # Boost if title contains key topic words
        topic_matches = {
            'crave': ['craving', 'cravings', 'urge', 'urges'],
            'stress': ['stress', 'stressed', 'anxiety', 'anxious'],
            'slip': ['slipped', 'relapse', 'smoked'],
            'badmood': ['mood', 'irritable', 'angry'],
            'support': ['help', 'support'],
        }

        for topic, variants in topic_matches.items():
            if topic in title_lower:
                # Check if message contains any variant of this topic
                if any(variant in message_lower for variant in variants):
                    score += 10.0  # Big boost for topic match
                    break

        # Boost for critical strategy content
        # If section contains specific evidence-based strategies, boost for relevant queries
        critical_strategies = {
            '4 d': (['craving', 'cravings', 'urge', 'urges', 'want', 'need', 'what should', 'what do'], 20.0),
            'breathing exercise': (['stress', 'stressed', 'anxiety', 'anxious'], 12.0),
        }

        for strategy, (query_terms, boost) in critical_strategies.items():
            if strategy in section_content_lower:
                if any(term in message_lower for term in query_terms):
                    score += boost  # Boost based on strategy importance
                    break

        return score
    
    def get_full_protocol(self) -> str:
        """Get the full protocol text"""
        return self.full_protocol
    
    def get_protocol_summary(self) -> str:
        """Get a summary of the protocol"""
        return f"""
QuitTxt Protocol Summary:
- Total sections: {len(self.sections)}
- Total length: {len(self.full_protocol)} characters
- Key topics: {', '.join(self.keyword_map.keys())}

This protocol guides conversations for a smoking cessation support program.
It includes message sequences, response templates, and strategies for helping
users quit smoking over a 6-month research study period.
"""
