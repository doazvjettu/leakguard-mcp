"""LG004 — Shuffled / non-temporal cross-validation split on time-series data."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import collect_constants, resolve_constant
from leakguard.core.findings import Severity
from leakguard.core.rules.base import Rule, RuleVisitor, called_method_name, get_kwarg

# Splitters that break temporal order (shuffle rows across the time axis).
_SHUFFLING_SPLITTERS = {"KFold", "StratifiedKFold", "ShuffleSplit", "RepeatedKFold", "RepeatedStratifiedKFold"}

# sklearn helpers whose `cv=<int>` silently builds a KFold over the rows. Even
# unshuffled, contiguous KFold trains later folds' models on earlier validation
# data and vice versa — only TimeSeriesSplit keeps train strictly before validate.
_CV_TAKING_CALLS = {
    "cross_val_score",
    "cross_validate",
    "cross_val_predict",
    "GridSearchCV",
    "RandomizedSearchCV",
}


def _is_false(node: cst.BaseExpression) -> bool:
    return isinstance(node, cst.Name) and node.value == "False"


class _Visitor(RuleVisitor):
    def visit_Module(self, node: cst.Module) -> None:
        # Constant env so `cv=N_FOLDS` with `N_FOLDS = 5` is seen.
        self._env = collect_constants(node)

    def visit_Call(self, node: cst.Call) -> None:
        # Splitters are usually imported bare (`train_test_split(...)`, `KFold(...)`).
        method = called_method_name(node, allow_bare=True)

        if method in _CV_TAKING_CALLS:
            cv = get_kwarg(node, "cv")
            if cv is None:
                return  # absent cv also defaults to KFold, but kept out of scope for now
            value = resolve_constant(cv.value, self._env)
            if isinstance(value, cst.Integer):
                self._emit(
                    node,
                    message=(
                        f"`{method}(..., cv={value.value})` silently builds a KFold over the rows. "
                        "Even unshuffled, its folds ignore time order: all but the last fold train "
                        "on data that comes after their validation rows — lookahead on temporal data."
                    ),
                    fix=f"Pass an explicit temporal splitter: `{method}(..., cv=TimeSeriesSplit(n_splits={value.value}))`.",
                )
            return

        if method == "train_test_split":
            shuffle = get_kwarg(node, "shuffle")
            # Default shuffle=True, so absent OR explicit True both reorder the data.
            if shuffle is None or not _is_false(shuffle.value):
                self._emit(
                    node,
                    message=(
                        "`train_test_split` shuffles by default, scattering future rows into the "
                        "train set and past rows into test. On time-series data this destroys the "
                        "temporal boundary and leaks the future into training."
                    ),
                    fix="Keep time order: `train_test_split(..., shuffle=False)` or use `TimeSeriesSplit`.",
                )
            return

        if method in _SHUFFLING_SPLITTERS:
            self._emit(
                node,
                message=(
                    f"`{method}` partitions rows without respecting time order, so each fold trains "
                    "on rows that occur after its validation rows — lookahead leakage on temporal data."
                ),
                fix="Use `TimeSeriesSplit(n_splits=...)`, which only ever trains on rows before each fold.",
            )


class LG004(Rule):
    id = "LG004"
    name = "shuffled-timeseries-split"
    severity = Severity.ERROR
    short = "train_test_split (default shuffle) or KFold instead of TimeSeriesSplit."
    explanation = (
        "Random splitters (train_test_split with its default shuffle=True, KFold, ShuffleSplit) "
        "assume rows are exchangeable. Time-series rows are not: shuffling places future "
        "observations in the training fold and evaluates on the past, leaking lookahead and "
        "inflating scores. TimeSeriesSplit (or an explicit ordered split / shuffle=False) keeps "
        "every training fold strictly before its validation fold."
    )
    fix_pattern = "from sklearn.model_selection import TimeSeriesSplit; TimeSeriesSplit(n_splits=5)"
    visitor_cls = _Visitor
