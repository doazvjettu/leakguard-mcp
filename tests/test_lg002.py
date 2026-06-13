"""LG002 — centered window."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg002_bad.py", "LG002")
    assert len(found) == 3  # rolling x2 + ewm, all center=True
    assert all(f.severity is Severity.ERROR for f in found)
    assert all(f.fix for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg002_clean.py", "LG002") == []


def test_center_false_not_flagged(guard):
    assert guard.scan("df['m'] = df['c'].rolling(5, center=False).mean()") == []


def test_center_true_flagged(guard):
    found = [f for f in guard.scan("x = s.rolling(5, center=True).mean()") if f.rule_id == "LG002"]
    assert len(found) == 1


def test_constant_center_flag_resolved(guard):
    code = "SMOOTH = True\nx = s.rolling(20, center=SMOOTH).mean()\n"
    found = [f for f in guard.scan(code) if f.rule_id == "LG002"]
    assert len(found) == 1


def test_constant_center_false_not_flagged(guard):
    code = "SMOOTH = False\nx = s.rolling(20, center=SMOOTH).mean()\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG002"] == []
