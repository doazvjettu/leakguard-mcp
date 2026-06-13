"""Server tool impls: JSON-safe shapes, catalog, explain, glob aggregation."""

import json

from leakguard import server
from tests.conftest import FIXTURES, load


def test_lint_code_returns_json_safe_envelope():
    out = server.lint_code_impl(load("lg001_bad.py"))
    json.dumps(out)
    assert out["ok"] is True and out["parse_error"] is None
    assert out["findings"] and out["findings"][0]["rule_id"] == "LG001"


def test_lint_code_surfaces_parse_error():
    out = server.lint_code_impl("def (: broken")
    assert out["ok"] is False and out["parse_error"]
    assert out["findings"] == []


def test_list_rules_has_all_ten_entries():
    rules = server.list_rules_impl()
    assert len(rules) == 10
    assert {r["id"] for r in rules} == {f"LG0{n:02d}" for n in range(1, 11)}
    assert all(set(r) == {"id", "name", "severity", "short"} for r in rules)


def test_all_rules_active_no_gating():
    # All rules run by default — a dataflow rule (LG003) must fire out of the box.
    code = "X = scaler.fit_transform(X)\na, b = train_test_split(X)\n"
    out = server.lint_code_impl(code)
    assert any(f["rule_id"] == "LG003" for f in out["findings"])


def test_explain_rule_known():
    out = server.explain_rule_impl("lg002")  # case-insensitive
    assert out["id"] == "LG002"
    assert out["explanation"] and out["fix_pattern"]


def test_explain_rule_unknown_returns_error_dict():
    out = server.explain_rule_impl("LG999")
    assert "error" in out and out["known"]


def test_lint_file_reads_from_disk():
    out = server.lint_file_impl(str(FIXTURES / "lg008_bad.py"))
    assert out["ok"] is True
    assert [r for r in out["findings"] if r["rule_id"] == "LG008"]


def test_lint_file_missing_returns_error_dict():
    out = server.lint_file_impl(str(FIXTURES / "does_not_exist.py"))
    assert out["ok"] is False and "error" in out and out["findings"] == []


def test_lint_paths_aggregates_by_path():
    out = server.lint_paths_impl(str(FIXTURES / "lg007_*.py"))
    json.dumps(out)
    bad = next(p for p in out if p.endswith("lg007_bad.py"))
    clean = next(p for p in out if p.endswith("lg007_clean.py"))
    assert [r for r in out[bad]["findings"] if r["rule_id"] == "LG007"]
    assert out[clean]["ok"] is True and out[clean]["findings"] == []
