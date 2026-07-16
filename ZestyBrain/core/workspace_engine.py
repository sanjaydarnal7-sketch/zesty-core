"""
Zesty OS
Workspace Engine
Version: 1.0

Mission 62

Manages the active workspace for Zesty OS.

Uses the Filesystem Engine for filesystem access.
"""

from __future__ import annotations

from pathlib import Path

from core.filesystem_engine import FilesystemEngine


class WorkspaceEngine:
    """
    Manages the current active workspace.
    """

    def __init__(self):

        self.fs = FilesystemEngine()

        self.workspace = Path.cwd()

    def current_path(self) -> Path:

        return self.workspace

    def workspace_name(self) -> str:

        return self.workspace.name

    def exists(self) -> bool:

        return self.fs.exists(self.workspace)

    def change_workspace(
        self,
        path: str | Path,
    ) -> Path:

        path = Path(path).resolve()

        if not path.exists():

            raise FileNotFoundError(
                f"Workspace does not exist: {path}"
            )

        if not path.is_dir():

            raise NotADirectoryError(
                f"Not a directory: {path}"
            )

        self.workspace = path

        return self.workspace

    def list_files(self) -> list[str]:

        return self.fs.list_directory(
            self.workspace
        )


# ------------------------------------------------------
# Self Test
# ------------------------------------------------------

if __name__ == "__main__":

    engine = WorkspaceEngine()

    print("===== WORKSPACE ENGINE TEST =====")
    print()

    print(
        "Workspace:",
        engine.workspace_name(),
    )

    print()

    print(
        "Path:",
        engine.current_path(),
    )

    print()

    print(
        "Exists:",
        engine.exists(),
    )

    print()

    files = engine.list_files()

    print(
        "Items:",
        len(files),
    )

    print()

    print("Mission 62 Passed")