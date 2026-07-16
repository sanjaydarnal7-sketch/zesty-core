"""
Zesty OS
Filesystem Engine
Version: 1.0

Mission 61

Provides safe filesystem operations
for the Zesty OS runtime.
"""

from __future__ import annotations

from pathlib import Path


class FilesystemEngine:
    """
    Safe filesystem engine.
    """

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return Path(path).exists()

    def create_directory(
        self,
        path: str | Path,
    ) -> Path:

        directory = Path(path)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def list_directory(
        self,
        path: str | Path,
    ) -> list[str]:

        directory = Path(path)

        if not directory.exists():

            return []

        return sorted(
            item.name
            for item in directory.iterdir()
        )

    def read_text(
        self,
        path: str | Path,
    ) -> str:

        file = Path(path)

        return file.read_text(
            encoding="utf-8"
        )

    def write_text(
        self,
        path: str | Path,
        content: str,
    ) -> None:

        file = Path(path)

        file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file.write_text(
            content,
            encoding="utf-8",
        )


# ------------------------------------------------------
# Self Test
# ------------------------------------------------------

if __name__ == "__main__":

    engine = FilesystemEngine()

    workspace = Path("filesystem_test")

    engine.create_directory(workspace)

    file = workspace / "hello.txt"

    engine.write_text(
        file,
        "Hello Zesty OS",
    )

    print("===== FILESYSTEM ENGINE TEST =====")
    print()

    print(
        "Exists :",
        engine.exists(file),
    )

    print(
        "Content:",
        engine.read_text(file),
    )

    print()

    print(
        "Directory:",
        engine.list_directory(workspace),
    )

    file.unlink()

    workspace.rmdir()

    print()

    print("Mission 61 Passed")