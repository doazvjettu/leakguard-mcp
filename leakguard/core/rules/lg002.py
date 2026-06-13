"""LG002 — Centered rolling/ewm window (center=True peeks at future rows)."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import collect_constants, resolve_constant
from leakguard.core.findings import Severity
from leakguard.core.rules.base import (
    Rule,
    RuleVisitor,
    called_method_name,
    get_kwarg,
    is_true_literal,
)

_WINDOW_METHODS = {"rolling", "ewm"}


class _Visitor(RuleVisitor):
    def visit_Module(self, node: cst.Module) -> None:
        # Simple constant propagation so `center=SMOOTH` with `SMOOTH = True` is seen.
        self._env = collect_constants(node)

    def visit_Call(self, node: cst.Call) -> None:
        method = called_method_name(node)
        if method not in _WINDOW_METHODS:
            return
        center = get_kwarg(node, "center")
        if center is None or not is_true_literal(resolve_constant(center.value, self._env)):
            return

        self._emit(
            node,
            message=(
                f"`{method}(..., center=True)` builds each window symmetrically around the "
                "current row, so it includes future observations. Every centered value leaks "
                "lookahead bias into the feature."
            ),
            fix=f"Drop center (defaults to a trailing window): `{method}(window)` without `center=True`.",
        )


class LG002(Rule):
    id = "LG002"
    name = "centered-window"
    severity = Severity.ERROR
    short = "rolling/ewm with center=True includes future rows in each window."
    explanation = (
        "A centered window places the label at the middle of the window, so half of the "
        "observations used to compute it are from the future relative to that row. In a "
        "backtest this silently leaks future information. Trailing windows (the default, "
        "center=False) only use past and current data."
    )
    fix_pattern = "df['ma'] = df['close'].rolling(20).mean()  # not rolling(20, center=True)"
    visitor_cls = _Visitor
