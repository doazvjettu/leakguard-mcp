"""Finding data model — JSON-safe, deterministic output contract.

One Finding == one pattern instance. Kept free of libcst/MCP types so the core stays
a pure value layer that any wrapper (MCP, CLI, pre-commit) can serialize directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Leakage confidence tier. `str` mixin keeps `.value` JSON-safe."""

    ERROR = "error"  # 🔴 almost certainly leakage
    WARNING = "warning"  # 🟡 suspicious, needs human review


@dataclass(frozen=True)
class Finding:
    """A single detected leakage pattern at a source location.

    Attributes mirror the output contract in CLAUDE.md: rule id, severity, line/col,
    a plain-English reason, and a concrete fix snippet the calling agent can apply.
    """

    rule_id: str
    name: str
    severity: Severity
    line: int
    col: int
    message: str  # why this is leakage, in plain English
    fix: str  # concrete fix snippet

    @property
    def sort_key(self) -> tuple[int, int, str]:
        # Deterministic ordering: source order first, then rule id as a stable tiebreak.
        return (self.line, self.col, self.rule_id)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "severity": self.severity.value,
            "line": self.line,
            "col": self.col,
            "message": self.message,
            "fix": self.fix,
        }
