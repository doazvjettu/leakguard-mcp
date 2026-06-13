"""LG010 — groupby aggregation across split boundary (ordering)."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg010_bad.py", "LG010")
    assert len(found) == 2  # groupby transform + groupby agg before split
    assert all(f.severity is Severity.WARNING for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg010_clean.py", "LG010") == []


def test_no_split_means_no_finding(guard):
    code = "g = df.groupby('s')['x'].transform('mean')\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG010"] == []


def test_plain_groupby_not_flagged_without_transform(guard):
    code = "a, b = train_test_split(df)\ng = df.groupby('s').mean()\n"
    # .mean() on a groupby isn't transform/agg shape → not LG010.
    assert [f for f in guard.scan(code) if f.rule_id == "LG010"] == []


def test_string_split_not_a_boundary(guard):
    # groupby-agg followed only by str.split() — no real split, no finding.
    code = "g = df.groupby('s')['x'].transform('mean')\nparts = name.split('_')\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG010"] == []


def test_expanding_lambda_not_flagged(guard):
    # Expanding-within-group only sees past rows — point-in-time safe.
    code = (
        "df['ma'] = df.groupby('sym')['r'].transform(lambda s: s.expanding().mean())\n"
        "a, b = train_test_split(df, shuffle=False)\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG010"] == []


def test_rolling_lambda_not_flagged(guard):
    code = (
        "df['ma'] = df.groupby('sym')['r'].transform(lambda s: s.rolling(20).mean())\n"
        "a, b = train_test_split(df, shuffle=False)\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG010"] == []


def test_full_sample_lambda_still_flagged(guard):
    # A z-score lambda uses whole-group statistics — still leaky across the split.
    code = (
        "df['z'] = df.groupby('s')['r'].transform(lambda s: (s - s.mean()) / s.std())\n"
        "a, b = train_test_split(df, shuffle=False)\n"
    )
    assert len([f for f in guard.scan(code) if f.rule_id == "LG010"]) == 1
