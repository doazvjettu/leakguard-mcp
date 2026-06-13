"""LG007 — backfill imputation."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg007_bad.py", "LG007")
    # bfill, fillna(bfill), fillna(backfill), interpolate(both), interpolate(backward)
    assert len(found) == 5
    assert all(f.severity is Severity.ERROR for f in found)
    assert all(f.fix for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg007_clean.py", "LG007") == []


def test_ffill_not_flagged(guard):
    assert guard.scan("df = df.fillna(method='ffill')") == []


def test_forward_interpolate_not_flagged(guard):
    assert guard.scan("df = df.interpolate(limit_direction='forward')") == []


def test_bare_user_function_named_bfill_not_flagged(guard):
    # A local helper named `bfill` is not the pandas method.
    assert [f for f in guard.scan("x = bfill(data)") if f.rule_id == "LG007"] == []
