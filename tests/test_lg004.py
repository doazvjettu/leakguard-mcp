"""LG004 — shuffled/non-temporal split."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg004_bad.py", "LG004")
    assert len(found) == 3  # default split, shuffle=True split, KFold
    assert all(f.severity is Severity.ERROR for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg004_clean.py", "LG004") == []


def test_default_shuffle_flagged(guard):
    found = [f for f in guard.scan("a = train_test_split(X, y)") if f.rule_id == "LG004"]
    assert len(found) == 1


def test_shuffle_false_not_flagged(guard):
    assert [f for f in guard.scan("a = train_test_split(X, y, shuffle=False)") if f.rule_id == "LG004"] == []


def test_cross_val_score_int_cv_flagged(guard):
    found = [f for f in guard.scan("s = cross_val_score(model, X, y, cv=5)") if f.rule_id == "LG004"]
    assert len(found) == 1


def test_cross_validate_int_cv_flagged(guard):
    found = [f for f in guard.scan("r = cross_validate(model, X, y, cv=3)") if f.rule_id == "LG004"]
    assert len(found) == 1


def test_grid_search_int_cv_flagged(guard):
    found = [f for f in guard.scan("g = GridSearchCV(model, grid, cv=5)") if f.rule_id == "LG004"]
    assert len(found) == 1


def test_constant_cv_resolved(guard):
    code = "N_FOLDS = 5\ns = cross_val_score(model, X, y, cv=N_FOLDS)\n"
    assert len([f for f in guard.scan(code) if f.rule_id == "LG004"]) == 1


def test_timeseries_split_cv_not_flagged(guard):
    code = "s = cross_val_score(model, X, y, cv=TimeSeriesSplit(n_splits=5))"
    assert [f for f in guard.scan(code) if f.rule_id == "LG004"] == []


def test_cross_val_score_without_cv_not_flagged(guard):
    # Absent cv also defaults to KFold, but flagging it is out of scope for now
    # (documented); only an explicit integer cv is matched.
    assert [f for f in guard.scan("s = cross_val_score(model, X, y)") if f.rule_id == "LG004"] == []
