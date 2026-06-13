"""LG001 — future-shift feature."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg001_bad.py", "LG001")
    assert len(found) == 4  # shift(-1), diff(-2), pct_change(-3), shift(periods=-1)
    assert all(f.severity is Severity.ERROR for f in found)
    assert all(f.fix for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg001_clean.py", "LG001") == []


def test_positive_shift_not_flagged(guard):
    assert guard.scan("df['x'] = df['c'].shift(1)") == []


def test_negative_shift_flagged(guard):
    found = [f for f in guard.scan("df['x'] = df['c'].shift(-1)") if f.rule_id == "LG001"]
    assert len(found) == 1
    assert found[0].line == 1


def test_bare_user_function_named_shift_not_flagged(guard):
    # A local helper that happens to be called `shift` is not the pandas method.
    assert [f for f in guard.scan("y = shift(-1)") if f.rule_id == "LG001"] == []


def test_constant_horizon_resolved(guard):
    code = "HORIZON = -5\ndf['fwd'] = df['close'].shift(HORIZON)\n"
    found = [f for f in guard.scan(code) if f.rule_id == "LG001"]
    assert len(found) == 1
    assert found[0].line == 2


def test_reassigned_constant_not_resolved(guard):
    # Ambiguous constant (reassigned) must not fire — conservative, avoids FPs.
    code = "H = -5\nH = 5\ndf['x'] = df['close'].shift(H)\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG001"] == []


def test_function_param_shadowing_not_resolved(guard):
    # A module constant must not leak into a function whose param shadows it.
    code = "H = -5\ndef feat(df, H):\n    return df['close'].shift(H)\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG001"] == []
