"""
Conversation History Sanitizer
"""

from __future__ import annotations

import re


class HistorySanitizer:

    REMOVE_PATTERNS = [
        r"\[TARGET_PANEL:.*?\]",
        r"\[FINAL REPLY\].*",
        r"\[DEBUG.*",
        r"\[OLLAMA.*",
        r"\[⏱.*",
        r"======================================================================.*",
    ]

    def sanitize(self, messages):

        cleaned = []

        for msg in messages:

            role = msg.get("role", "")
            content = msg.get("content", "")

            if not content:
                continue

            for pattern in self.REMOVE_PATTERNS:
                content = re.sub(
                    pattern,
                    "",
                    content,
                    flags=re.MULTILINE,
                )

            content = re.sub(r"\n{3,}", "\n\n", content)
            content = content.strip()

            if not content:
                continue

            cleaned.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        # remove consecutive duplicates

        final = []

        previous = None

        for item in cleaned:

            if previous == item["content"]:
                continue

            final.append(item)
            previous = item["content"]

        return final
