"""
Zesty OS
Teaching Studio
Version: 1.0

Mission 40

Provides structured teaching sessions for Zesty.
Training is stored inside a temporary workspace
until the user decides to archive or promote it.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Optional
import uuid


@dataclass
class TrainingNote:

    id: str

    topic: str

    content: str

    created_at: str


@dataclass
class TrainingWorkspace:

    id: str

    name: str

    goal: str

    active: bool = True

    notes: List[TrainingNote] = field(default_factory=list)


class TeachingStudio:

    def __init__(self):

        self.workspace: Optional[TrainingWorkspace] = None

    def start_training(self, name: str, goal: str):

        self.workspace = TrainingWorkspace(

            id=str(uuid.uuid4()),

            name=name,

            goal=goal,

            active=True

        )

        return self.workspace

    def add_note(self, topic: str, content: str):

        if self.workspace is None:

            raise RuntimeError(
                "No active training workspace."
            )

        note = TrainingNote(

            id=str(uuid.uuid4()),

            topic=topic,

            content=content,

            created_at=datetime.now(UTC).isoformat()

        )

        self.workspace.notes.append(note)

        return note

    def summary(self):

        if self.workspace is None:

            return {

                "status": "no_workspace"

            }

        return {

            "workspace": self.workspace.name,

            "goal": self.workspace.goal,

            "notes": len(self.workspace.notes),

            "active": self.workspace.active

        }

    def list_notes(self):

        if self.workspace is None:

            return []

        return self.workspace.notes

    def finish_training(self):

        if self.workspace:

            self.workspace.active = False

        return self.workspace


if __name__ == "__main__":

    studio = TeachingStudio()

    studio.start_training(

        name="Bar Mystério Competition",

        goal="Prepare complete cocktail presentation."

    )

    studio.add_note(

        "Story",

        "The cocktail represents collaboration between Sanjay and Jessie."

    )

    studio.add_note(

        "Judges",

        "Explain that AI supported research while Sanjay crafted the final drink."

    )

    studio.add_note(

        "Humor",

        "Keep jokes light and situational."

    )

    print("===== TEACHING STUDIO =====")

    print()

    print(studio.summary())

    print()

    for note in studio.list_notes():

        print(note)

        print("-" * 60)

    studio.finish_training()

    print()

    print("===== TRAINING CLOSED =====")

    print()

    print(studio.summary())