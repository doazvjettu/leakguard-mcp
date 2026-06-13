"""LG003 — global-fit scaling before split (ordering)."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg003_bad.py", "LG003")
    assert len(found) == 2  # fit_transform + scaler.fit, both before split
    assert all(f.severity is Severity.ERROR for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg003_clean.py", "LG003") == []


def test_no_split_means_no_finding(guard):
    # Without a split in the file we cannot assert the ordering leak.
    code = "scaler = StandardScaler()\nX = scaler.fit_transform(X)\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_model_fit_not_flagged(guard):
    # A plain estimator .fit() (no scaler-like receiver) is not LG003.
    code = "Xtr, Xte = train_test_split(X, y)\nmodel.fit(Xtr, ytr)\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_string_split_does_not_suppress_real_finding(guard):
    # str.split() before the fit must not count as the train/test boundary.
    code = (
        "cols = header.split(',')\n"
        "X = scaler.fit_transform(X)\n"
        "a, b = train_test_split(X)\n"
    )
    assert len([f for f in guard.scan(code) if f.rule_id == "LG003"]) == 1


def test_string_split_alone_creates_no_finding(guard):
    # fit before only a str.split() (no real split in file) must not flag.
    code = "X = scaler.fit_transform(X)\nparts = line.split(',')\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_cv_splitter_split_counts_as_boundary(guard):
    code = "X = scaler.fit_transform(X)\nfor tr, te in tscv.split(X): pass\n"
    assert len([f for f in guard.scan(code) if f.rule_id == "LG003"]) == 1


def test_kwarg_only_fit_not_flagged(guard):
    # .fit(y=...) has no positional arg — not a transformer-style fit.
    code = "model.fit(y=labels)\na, b = train_test_split(X)\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_handrolled_zscore_before_split_flagged(guard):
    code = (
        "mu = features.mean()\n"
        "sigma = features.std()\n"
        "features_z = (features - mu) / sigma\n"
        "a, b = train_test_split(features_z, shuffle=False)\n"
    )
    found = [f for f in guard.scan(code) if f.rule_id == "LG003"]
    assert len(found) == 1
    assert found[0].line == 3


def test_inline_minmax_before_split_flagged(guard):
    code = (
        "X_norm = (X - X.min()) / (X.max() - X.min())\n"
        "a, b = train_test_split(X_norm, shuffle=False)\n"
    )
    assert len([f for f in guard.scan(code) if f.rule_id == "LG003"]) == 1


def test_normalization_after_split_not_flagged(guard):
    code = (
        "tr, te = train_test_split(X, shuffle=False)\n"
        "mu = tr.mean()\n"
        "tr_z = (tr - mu) / tr.std()\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_normalization_without_split_not_flagged(guard):
    code = "mu = X.mean()\nX_z = (X - mu) / X.std()\n"
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_rolling_stats_in_expression_not_flagged(guard):
    # Trailing-window stats are point-in-time safe; receiver is a call, not a frame.
    code = (
        "df['z'] = (df['r'] - df['r'].rolling(60).mean()) / df['r'].rolling(60).std()\n"
        "a, b = train_test_split(df, shuffle=False)\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []


def test_groupby_lambda_zscore_not_lg003(guard):
    # Group-wise zscore is LG010's territory; LG003 must not double-fire on it.
    code = (
        "df['z'] = df.groupby('s')['r'].transform(lambda s: (s - s.mean()) / s.std())\n"
        "a, b = train_test_split(df, shuffle=False)\n"
    )
    assert [f for f in guard.scan(code) if f.rule_id == "LG003"] == []
