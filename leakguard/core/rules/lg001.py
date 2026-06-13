"""LG001 — Future shift as feature (negative-period shift/diff/pct_change)."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import collect_constants, resolve_constant
from leakguard.core.findings import Severity
from leakguard.core.rules.base import (
    Rule,
    RuleVisitor,
    called_method_name,
    first_positional,
    get_kwarg,
    negative_int_value,
)

_SHIFT_METHODS = {"shift", "diff", "pct_change"}


class _Visitor(RuleVisitor):
    def visit_Module(self, node: cst.Module) -> None:
        # Simple constant propagation so `shift(HORIZON)` with `HORIZON = -5` is seen.
        self._env = collect_constants(node)

    def visit_Call(self, node: cst.Call) -> None:
        method = called_method_name(node)
        if method not in _SHIFT_METHODS:
            return

        # `periods` is the first positional arg for all three methods, or the kw `periods=`.
        periods_arg = get_kwarg(node, "periods") or first_positional(node)
        if periods_arg is None:
            return
        n = negative_int_value(resolve_constant(periods_arg.value, self._env))
        if n is None:
            return

        self._emit(
            node,
            message=(
                f"`{method}(-{n})` pulls a value from {n} row(s) in the future into the "
                "current row. If this feeds a feature/X column it leaks lookahead bias. "
                "(Heuristic: a legitimate forward-return *label* also uses a negative shift "
                "— review whether this column is a target, not a feature.)"
            ),
            fix=(
                f"Use a non-negative shift for features: `{method}({n})` (past) or build the "
                "forward value only as a prediction target, never as model input."
            ),
        )


class LG001(Rule):
    id = "LG001"
    name = "future-shift-feature"
    severity = Severity.ERROR
    short = "Negative-period shift/diff/pct_change pulls future values into a row."
    explanation = (
        "shift(-n), diff(-n) and pct_change(-n) move data backward in time, exposing the "
        "current row to values that only exist n steps in the future. Used as a feature this "
        "is direct lookahead leakage. The only safe use of a negative shift is constructing a "
        "prediction *target* (e.g. forward return) that is never also fed back as input."
    )
    fix_pattern = "df['feat'] = df['close'].shift(1)  # past, not df['close'].shift(-1)"
    visitor_cls = _Visitor
