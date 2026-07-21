"""
Relationship Engine
"""

from __future__ import annotations

from typing import Dict

from .models import Person


class RelationshipEngine:

    def __init__(self):

        self.people: Dict[str, Person] = {}

    def remember_person(
        self,
        name,
        relationship,
        organization="",
        importance=5,
    ):

        key = name.lower()

        if key not in self.people:

            self.people[key] = Person(
                name=name,
                relationship=relationship,
                organization=organization,
                importance=importance,
            )

        return self.people[key]

    def add_note(self, name, note):

        person = self.people.get(name.lower())

        if person:
            person.notes.append(note)

    def add_preference(self, name, pref):

        person = self.people.get(name.lower())

        if person:
            person.preferences.append(pref)

    def get(self, name):

        return self.people.get(name.lower())

    def all_people(self):

        return list(self.people.values())
