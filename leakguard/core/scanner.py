"""LeakGuard.scan() — the stateless pure-Python entry point. No MCP imports.

Parses source once with libcst, runs every registered rule visitor over the shared
metadata wrapper, and returns deterministically-ordered Findings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import libcst as cst

from leakguard.core.findings import Finding
from leakguard.core.rules import RULES, Rule

logger = logging.getLogger("leakguard")


@dataclass(frozen=True)
class ScanResult:
    """Scan outcome that distinguishes 'clean' from 'could not parse'.

    A consumer that only looks at `findings` would mistake a syntax-broken file for a
    leak-free one — `ok`/`parse_error` make that state explicit.
    """

    findings: list[Finding] = field(default_factory=list)
    parse_error: str | None = None

    @property
    def ok(self) -> bool:
        return self.parse_error is None

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "parse_error": self.parse_error,
            "findings": [f.to_dict() for f in self.findings],
        }


class LeakGuard:
    """Stateless scanner. Construct once, call `scan()` for any source string.

    `rules` lets a caller run a subset (e.g. a CLI `--select` filter); defaults to all rules.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = list(RULES) if rules is None else list(rules)

    def scan_result(self, code: str, filename: str | None = None) -> ScanResult:
        """Full outcome: findings plus an explicit parse-error state."""
        try:
            module = cst.parse_module(code)
        except cst.ParserSyntaxError as exc:
            # We report leakage, not syntax — but the caller must be able to tell
            # "clean" from "unparseable", so the error is carried, not swallowed.
            logger.warning("leakguard: unparseable source %s: %s", filename or "<code>", exc)
            return ScanResult(parse_error=str(exc))

        wrapper = cst.MetadataWrapper(module)
        findings: list[Finding] = []
        for rule in self.rules:
            visitor = rule.visitor()
            wrapper.visit(visitor)
            findings.extend(visitor.findings)

        findings.sort(key=lambda f: f.sort_key)
        return ScanResult(findings=findings)

    def scan(self, code: str, filename: str | None = None) -> list[Finding]:
        """Findings only (parse errors yield an empty list — use scan_result to see them)."""
        return self.scan_result(code, filename).findings

    def scan_to_json(self, code: str, filename: str | None = None) -> list[dict]:
        return [f.to_dict() for f in self.scan(code, filename)]
