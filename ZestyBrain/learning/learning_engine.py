"""
Learning Engine V2
Structured fact extraction.
"""

import re

from .models import Fact, LearningResult


class LearningEngine:

    RELATIONSHIP_PATTERNS = [
        ("friend", r"my friend\s+([A-Z][a-zA-Z]+)"),
        ("father", r"my father\s+([A-Z][a-zA-Z]+)"),
        ("mother", r"my mother\s+([A-Z][a-zA-Z]+)"),
        ("sister", r"my sister\s+([A-Z][a-zA-Z]+)"),
        ("brother", r"my brother\s+([A-Z][a-zA-Z]+)"),
        ("wife", r"my wife\s+([A-Z][a-zA-Z]+)"),
        ("husband", r"my husband\s+([A-Z][a-zA-Z]+)"),
        ("boss", r"my boss\s+([A-Z][a-zA-Z]+)"),
        ("client", r"my client\s+([A-Z][a-zA-Z]+)"),
        ("investor", r"my investor\s+([A-Z][a-zA-Z]+)"),
    ]

    def classify(self, text: str) -> LearningResult:

        result = LearningResult()
        lower = text.lower()

        if any(x in lower for x in ["haha", "lol", "thanks", "thank you", "ok", "okay"]):
            result.ignored = True
            return result

        m = re.search(r"my name is\s+(.+?)[\.\!\?]?$", text, re.IGNORECASE)
        if m:
            result.identities.append(
                Fact(
                    type="name",
                    value=m.group(1).strip(),
                    confidence=0.99,
                )
            )

        m = re.search(r"my company is\s+(.+?)[\.\!\?]?$", text, re.IGNORECASE)
        if m:
            result.identities.append(
                Fact(
                    type="company",
                    value=m.group(1).strip(),
                    confidence=0.99,
                )
            )

        for relation, pattern in self.RELATIONSHIP_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                result.relationships.append(
                    Fact(
                        type=relation,
                        value=m.group(1).strip(),
                        confidence=0.98,
                    )
                )

        if any(x in lower for x in [
            "today",
            "tomorrow",
            "currently",
            "right now",
            "this week",
        ]):
            result.events.append(
                Fact(
                    type="event",
                    value=text.strip(),
                    confidence=0.95,
                )
            )

        return result
