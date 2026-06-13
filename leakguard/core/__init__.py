"""Pure leakage-scanning core. No MCP / server dependencies live in this package."""

from leakguard.core.findings import Finding, Severity
from leakguard.core.rules import RULES, RULES_BY_ID
from leakguard.core.rules.base import Rule
from leakguard.core.scanner import LeakGuard, ScanResult

__all__ = ["LeakGuard", "ScanResult", "Finding", "Severity", "Rule", "RULES", "RULES_BY_ID"]
