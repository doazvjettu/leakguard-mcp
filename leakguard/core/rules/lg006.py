"""LG006 — Whole-history reduction on a column used as a per-row feature."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import chain_calls_method, subscript_string_key
from leakguard.core.findings import Severity
from leakguard.core.rules.base import Rule, RuleVisitor, called_method_name

# Full-series reductions that collapse the entire history into one number.
_REDUCERS = {"max", "min", "mean", "std", "median", "var", "sum", "quantile"}


class _Visitor(RuleVisitor):
    def visit_Call(self, node: cst.Call) -> None:
        method = called_method_name(node)
        if method not in _REDUCERS:
            return
        func = node.func
        if not isinstance(func, cst.Attribute):
            return
        # Receiver must be a bare column `df['col']`. A windowed receiver
        # (`df['col'].rolling(20).max()`) is a Call, not a subscript, so it is skipped.
        col = subscript_string_key(func.value)
        if col is None:
            return
        # A grouped reduction (`df.groupby('k')['col'].mean()`) is one value per group,
        # not a whole-history broadcast — cross-split grouping is LG010's territory.
        if chain_calls_method(node, "groupby"):
            return

        self._emit(
            node,
            message=(
                f"`['{col}'].{method}()` reduces the entire column — including future rows — "
                "to one number. Using that as a per-row feature leaks the whole history "
                "(e.g. an all-time high/low or global z-score the model could not know yet)."
            ),
            fix=f"Use an expanding (point-in-time) reduction: `df['{col}'].expanding().{method}()`.",
        )


class LG006(Rule):
    id = "LG006"
    name = "whole-history-aggregate"
    severity = Severity.WARNING
    short = "Full-column max/min/mean/std/quantile used as a feature sees the whole series."
    explanation = (
        "A reduction taken over an entire column (df['close'].max(), .mean(), .quantile(), …) "
        "summarizes the full history at once, future included. Broadcast back as a per-row "
        "feature it leaks information that was not available at each row's timestamp. The "
        "point-in-time-safe form is an expanding (or trailing rolling) reduction, which at row "
        "t only sees rows up to t."
    )
    fix_pattern = "df['hi'] = df['close'].expanding().max()  # not df['close'].max()"
    visitor_cls = _Visitor
