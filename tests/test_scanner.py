"""Scanner contract: empty/syntax-error handling, determinism, JSON-safety."""

import json

from tests.conftest import load


def test_empty_code_returns_no_findings(guard):
    assert guard.scan("") == []


def test_whitespace_only_returns_no_findings(guard):
    assert guard.scan("\n   \n") == []


def test_syntax_error_returns_empty_not_raises(guard):
    # Unparseable source must not crash the agent loop.
    assert guard.scan("def (: this is not python") == []


def test_scan_result_distinguishes_parse_error_from_clean(guard):
    broken = guard.scan_result("def (: nope")
    assert broken.ok is False and broken.parse_error and broken.findings == []
    clean = guard.scan_result("x = 1")
    assert clean.ok is True and clean.parse_error is None
    d = broken.to_dict()
    assert d["ok"] is False and d["parse_error"]


def test_output_is_json_serializable(guard):
    rows = guard.scan_to_json(load("lg001_bad.py"))
    json.dumps(rows)  # must not raise
    assert rows and all(set(r) >= {"rule_id", "severity", "line", "col", "message", "fix"} for r in rows)


def test_severity_serializes_as_plain_string(guard):
    rows = guard.scan_to_json(load("lg002_bad.py"))
    assert all(r["severity"] in ("error", "warning") for r in rows)


def test_deterministic_ordering(guard):
    code = load("lg007_bad.py")
    first = [f.sort_key for f in guard.scan(code)]
    second = [f.sort_key for f in guard.scan(code)]
    assert first == second == sorted(first)


def test_findings_sorted_by_position(guard):
    # A file mixing rules should still come back in (line, col) order.
    code = "import pandas as pd\n" + load("lg008_bad.py")
    keys = [f.sort_key for f in guard.scan(code)]
    assert keys == sorted(keys)
