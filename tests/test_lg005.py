"""LG005 — label leakage (future-derived column reused as feature)."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_bad(guard):
    found = findings_for(guard, "lg005_bad.py", "LG005")
    assert len(found) == 1  # fwd_ret reused in X
    assert found[0].severity is Severity.ERROR


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg005_clean.py", "LG005") == []


def test_past_only_features_not_flagged(guard):
    code = "df['mom'] = df['close'].pct_change(5)\nX = df[['mom']]\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG005"] == []


def test_constant_horizon_taint_resolved(guard):
    code = (
        "H = -5\n"
        "df['fwd'] = df['close'].shift(H)\n"
        "X = df[['mom', 'fwd']]\n"
    )
    found = [f for f in guard.scan(code) if f.rule_id == "LG005"]
    assert len(found) == 1


def test_drop_that_keeps_target_flagged(guard):
    code = (
        "df['fwd'] = df['close'].shift(-1)\n"
        "X = df.drop(columns=['date', 'symbol'])\n"
    )
    found = [f for f in guard.scan(code) if f.rule_id == "LG005"]
    assert len(found) == 1
    assert found[0].line == 2


def test_drop_that_removes_target_not_flagged(guard):
    code = (
        "df['fwd'] = df['close'].shift(-1)\n"
        "X = df.drop(columns=['fwd'])\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG005"] == []


def test_drop_axis1_positional_flagged(guard):
    code = (
        "df['fwd'] = df['close'].shift(-1)\n"
        "X = df.drop(['date'], axis=1)\n"
    )
    assert len([f for f in guard.scan(code) if f.rule_id == "LG005"]) == 1


def test_bare_drop_statement_not_flagged(guard):
    # Not assigned anywhere — no feature matrix is being built from it.
    code = (
        "df['fwd'] = df['close'].shift(-1)\n"
        "df.drop(columns=['date'], inplace=True)\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG005"] == []


def test_row_drop_not_flagged(guard):
    code = (
        "df['fwd'] = df['close'].shift(-1)\n"
        "X = df.drop(index=[0, 1])\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG005"] == []
