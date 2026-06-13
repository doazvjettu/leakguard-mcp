"""LG007 — Backfill imputation pulls future values backward to fill gaps."""

from __future__ import annotations

import libcst as cst

from leakguard.core.findings import Severity
from leakguard.core.rules.base import (
    Rule,
    RuleVisitor,
    called_method_name,
    get_kwarg,
    string_value,
)

_BACKFILL_FILLNA = {"bfill", "backfill"}
_BACKWARD_INTERP = {"both", "backward"}


class _Visitor(RuleVisitor):
    def visit_Call(self, node: cst.Call) -> None:
        method = called_method_name(node)
        if method is None:
            return

        # Direct backfill call: .bfill(...)
        if method == "bfill":
            self._emit(node, *self._msg("`.bfill()`"))
            return

        # fillna(method='bfill'|'backfill')
        if method == "fillna":
            m = get_kwarg(node, "method")
            if m is not None and string_value(m.value) in _BACKFILL_FILLNA:
                self._emit(node, *self._msg(f"`fillna(method={string_value(m.value)!r})`"))
            return

        # interpolate(limit_direction='both'|'backward')
        if method == "interpolate":
            d = get_kwarg(node, "limit_direction")
            if d is not None and string_value(d.value) in _BACKWARD_INTERP:
                self._emit(
                    node, *self._msg(f"`interpolate(limit_direction={string_value(d.value)!r})`")
                )
            return

    @staticmethod
    def _msg(call_desc: str) -> tuple[str, str]:
        message = (
            f"{call_desc} fills missing values using later (future) observations, copying "
            "information backward in time. Any row imputed this way leaks data that was not "
            "available at that timestamp."
        )
        fix = "Use forward fill instead: `.ffill()` / `fillna(method='ffill')` / forward interpolation."
        return message, fix


class LG007(Rule):
    id = "LG007"
    name = "backfill-imputation"
    severity = Severity.ERROR
    short = "bfill / fillna(method='bfill') / backward interpolate copies future values back."
    explanation = (
        "Backward filling resolves a gap by reaching into the future for the next known value. "
        "At the imputed timestamp that value did not yet exist, so the model trains on "
        "information it could not have had live. Forward fill (ffill) only carries past values "
        "forward and is point-in-time safe."
    )
    fix_pattern = "df = df.ffill()  # not df.bfill() / fillna(method='bfill')"
    visitor_cls = _Visitor
