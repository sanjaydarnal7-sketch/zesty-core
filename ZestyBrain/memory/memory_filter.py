"""
Memory Filter
Removes noisy, repetitive and identity-breaking memories
before they reach the LLM.
"""

from __future__ import annotations

import re


class MemoryFilter:

    DROP_PATTERNS = [

        r"(?i)^namaste.*",
        r"(?i)^hello.*",
        r"(?i)^hi.*",
        r"(?i)^hey there.*",
        r"(?i)^greetings.*",

        r"(?i).*main zesty.*",
        r"(?i).*advanced operational intelligence.*",
        r"(?i).*language model.*",
        r"(?i).*artificial intelligence.*",
        r"(?i).*ai assistant.*",
        r"(?i).*aapke saath baat.*",
        r"(?i).*mujhe khushi.*",
        r"(?i).*main aapki.*madad.*",
        r"(?i).*kya jaanna chahte.*",
        r"(?i).*taiyaar hoon.*",

    ]

    def filter(self, documents):

        if not documents:
            return []

        cleaned = []

        seen = set()

        for text in documents:

            if not text:
                continue

            text = re.sub(r'\s+', ' ', text).strip()

            if text.lower().startswith("data:"):
                text = text[5:].strip()

            reject = False

            for pattern in self.DROP_PATTERNS:
                if re.search(pattern, text):
                    reject = True
                    break

            if reject:
                continue

            if text in seen:
                continue

            seen.add(text)

            cleaned.append(text)

        return cleaned
