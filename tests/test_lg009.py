"""LG009 — resample label/closed mismatch."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg009_bad.py", "LG009")
    assert len(found) == 3  # last, ohlc, agg without label='right'
    assert all(f.severity is Severity.WARNING for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg009_clean.py", "LG009") == []


def test_label_right_not_flagged(guard):
    code = "b = df.resample('1h', label='right').last()"
    assert [f for f in guard.scan(code) if f.rule_id == "LG009"] == []


def test_resample_without_agg_not_flagged(guard):
    # A bare resampler with no aggregation isn't actionable.
    assert [f for f in guard.scan("r = df.resample('1h')") if f.rule_id == "LG009"] == []
