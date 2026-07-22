"""
Zesty Fact Memory

Structured long-term memory backed by SQLite.
"""

from __future__ import annotations

from ZestyBrain.memory.fact_store import FactStore


class FactMemory:

    def __init__(self):

        self.store = FactStore()

        self.identities = {}
        self.relationships = {}
        self.preferences = {}
        self.goals = {}
        self.events = []

        self._restore()

    def _restore(self):

        for category, key, value in self.store.load():

            if category == "identity":
                self.identities[key] = value

            elif category == "relationship":
                self.relationships.setdefault(key, [])
                if value not in self.relationships[key]:
                    self.relationships[key].append(value)

            elif category == "preference":
                self.preferences[key] = value

            elif category == "goal":
                self.goals[key] = value

            elif category == "event":
                self.events.append(value)

    def remember_identity(self, key: str, value: str):

        self.identities[key] = value
        self.store.remember("identity", key, value)

    def remember_relationship(self, relation: str, person: str):

        self.relationships.setdefault(relation, [])

        if person not in self.relationships[relation]:
            self.relationships[relation].append(person)

        self.store.remember("relationship", relation, person)

    def remember_preference(self, key: str, value: str):

        self.preferences[key] = value
        self.store.remember("preference", key, value)

    def remember_goal(self, key: str, value: str):

        self.goals[key] = value
        self.store.remember("goal", key, value)

    def remember_event(self, event: str):

        event = event.strip()

        if not event:
            return

        if event in self.events:
            return

        self.events.append(event)
        self.store.remember("event", "event", event)

    def snapshot(self):

        return {
            "identity": self.identities,
            "relationships": self.relationships,
            "preferences": self.preferences,
            "goals": self.goals,
            "events": self.events,
        }


    def prompt_context(self) -> str:

        data = self.snapshot()

        lines = []

        if data["identity"]:
            lines.append("IDENTITY")
            for k, v in data["identity"].items():
                lines.append(f"- {k}: {v}")

        if data["relationships"]:
            lines.append("\nRELATIONSHIPS")
            for k, vals in data["relationships"].items():
                lines.append(f"- {k}: {', '.join(vals)}")

        if data["preferences"]:
            lines.append("\nPREFERENCES")
            for k, v in data["preferences"].items():
                lines.append(f"- {k}: {v}")

        if data["goals"]:
            lines.append("\nGOALS")
            for k, v in data["goals"].items():
                lines.append(f"- {k}: {v}")

        if data["events"]:
            lines.append("\nRECENT EVENTS")
            for e in data["events"][-10:]:
                lines.append(f"- {e}")

        return "\n".join(lines)
