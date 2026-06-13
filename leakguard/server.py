"""FastMCP wrapper. Thin layer over leakguard.core — no detection logic lives here.

Exposes 5 tools: lint_code, lint_file, lint_paths, list_rules, explain_rule. The actual
work lives in plain `_impl` functions (directly unit-testable); FastMCP just registers
them as tools, keeping the MCP surface decoupled from the logic.

Lint tools return an envelope `{ok, parse_error, findings}` (plus `error` for unreadable
files) so an agent can distinguish clean code from code we failed to analyze.
"""

from __future__ import annotations

import glob as globlib
import sys

from fastmcp import FastMCP

from leakguard.core import RULES, RULES_BY_ID, LeakGuard

# All 10 rules, free for everyone.
_guard = LeakGuard()


def lint_code_impl(code: str, filename: str | None = None) -> dict:
    """Scan a source string for leakage patterns. Returns {ok, parse_error, findings}."""
    return _guard.scan_result(code, filename).to_dict()


def lint_file_impl(path: str) -> dict:
    """Scan a single file on disk. Returns {ok, parse_error, findings} or an error dict."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            code = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        return {"ok": False, "error": f"cannot read {path}: {exc}", "findings": []}
    return _guard.scan_result(code, filename=path).to_dict()


def lint_paths_impl(pattern: str) -> dict[str, dict]:
    """Scan every file matching a glob. Returns {path: {ok, parse_error, findings}}."""
    results: dict[str, dict] = {}
    for path in sorted(globlib.glob(pattern, recursive=True)):
        results[path] = lint_file_impl(path)
    return results


def list_rules_impl() -> list[dict]:
    """Full rule catalog with id, name, severity, and one-line summary."""
    return [rule.catalog_entry() for rule in RULES]


def explain_rule_impl(rule_id: str) -> dict:
    """Long-form rationale and canonical fix pattern for one rule id (e.g. 'LG001')."""
    rule = RULES_BY_ID.get(rule_id.upper())
    if rule is None:
        return {"error": f"unknown rule id: {rule_id!r}", "known": sorted(RULES_BY_ID)}
    return {
        "id": rule.id,
        "name": rule.name,
        "severity": rule.severity.value,
        "explanation": rule.explanation,
        "fix_pattern": rule.fix_pattern,
    }


mcp = FastMCP("leakguard")
mcp.tool(name="lint_code")(lint_code_impl)
mcp.tool(name="lint_file")(lint_file_impl)
mcp.tool(name="lint_paths")(lint_paths_impl)
mcp.tool(name="list_rules")(list_rules_impl)
mcp.tool(name="explain_rule")(explain_rule_impl)


def main() -> None:
    # Banner to stderr — stdout belongs to the stdio MCP transport.
    print(f"leakguard: {len(RULES)} rules active", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
