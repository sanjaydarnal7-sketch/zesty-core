"""
Zesty OS
Conversation Manager
Version: 1.0

Mission 23
"""

from typing import Dict, List


class ConversationManager:

    def __init__(self, max_messages: int = 8):

        self.max_messages = max_messages

        self.history: List[Dict[str, str]] = []

    def add_user(self, text: str):

        self.history.append({
            "role": "user",
            "content": text
        })

        self._trim()

    def add_assistant(self, text: str):

        self.history.append({
            "role": "assistant",
            "content": text
        })

        self._trim()

    def get_history(self):

        return list(self.history)

    def clear(self):

        self.history.clear()

    def _trim(self):

        while len(self.history) > self.max_messages:
            self.history.pop(0)


if __name__ == "__main__":

    memory = ConversationManager()

    memory.add_user("Hello")

    memory.add_assistant("Hi Sanjay")

    print(memory.get_history())