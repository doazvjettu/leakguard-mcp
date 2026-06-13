"""LG006 — whole-history aggregate as feature."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg006_bad.py", "LG006")
    assert len(found) == 4  # max, min, mean, std on full columns
    assert all(f.severity is Severity.WARNING for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg006_clean.py", "LG006") == []


def test_expanding_not_flagged(guard):
    assert [f for f in guard.scan("df['h'] = df['c'].expanding().max()") if f.rule_id == "LG006"] == []


def test_full_column_max_flagged(guard):
    found = [f for f in guard.scan("df['h'] = df['c'].max()") if f.rule_id == "LG006"]
    assert len(found) == 1


def test_groupby_reduction_not_flagged(guard):
    # Per-group reduction is not a whole-history broadcast; cross-split grouping
    # is LG010's territory, and here it runs on the train partition anyway.
    code = "mu = train.groupby('sector')['ret'].mean()"
    assert [f for f in guard.scan(code) if f.rule_id == "LG006"] == []


def test_groupby_quantile_not_flagged(guard):
    code = "q = df.groupby('sym')['vol'].quantile(0.9)"
    assert [f for f in guard.scan(code) if f.rule_id == "LG006"] == []
