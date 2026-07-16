"""
Zesty OS
Validation Engine
Version: 1.0

Mission 60

Validates the core infrastructure of Zesty OS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ValidationResult:
    """
    Result of a single validation.
    """

    name: str
    passed: bool
    message: str


class ValidationEngine:
    """
    Validates the core runtime.
    """

    def __init__(self):

        self.root = Path(__file__).parent.parent

    def validate(self) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        results.append(
            self._check_file(
                "Capability Registry",
                "capabilities/registry.py",
            )
        )

        results.append(
            self._check_file(
                "Capability Manager",
                "capabilities/manager.py",
            )
        )

        results.append(
            self._check_file(
                "Guardian Policy",
                "guardian/policy.py",
            )
        )

        results.append(
            self._check_file(
                "Guardian Controller",
                "guardian/controller.py",
            )
        )

        results.append(
            self._check_file(
                "Logging Engine",
                "core/logging_engine.py",
            )
        )

        results.append(
            self._check_file(
                "System Health Capability",
                "capabilities/native/system_health.py",
            )
        )

        results.append(
            self._check_file(
                "Time Capability",
                "capabilities/native/time_capability.py",
            )
        )

        return results

    def _check_file(
        self,
        name: str,
        relative_path: str,
    ) -> ValidationResult:

        file_path = self.root / relative_path

        if file_path.exists():

            return ValidationResult(
                name=name,
                passed=True,
                message="OK",
            )

        return ValidationResult(
            name=name,
            passed=False,
            message="Missing",
        )


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    engine = ValidationEngine()

    results = engine.validate()

    print("===== VALIDATION ENGINE TEST =====")
    print()

    passed = 0

    for result in results:

        status = "PASS" if result.passed else "FAIL"

        print(
            f"[{status}] {result.name} - {result.message}"
        )

        if result.passed:

            passed += 1

    print()

    print(
        f"Overall: {passed}/{len(results)} Checks Passed"
    )

    if passed == len(results):

        print("SYSTEM STATUS: HEALTHY")

    else:

        print("SYSTEM STATUS: ATTENTION REQUIRED")