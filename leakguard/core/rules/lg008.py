"""LG008 — Forward/nearest merge_asof joins match against future rows."""

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

_FORWARD_DIRECTIONS = {"forward", "nearest"}


class _Visitor(RuleVisitor):
    def visit_Call(self, node: cst.Call) -> None:
        # merge_asof appears both as pd.merge_asof(...) and imported bare.
        if called_method_name(node, allow_bare=True) != "merge_asof":
            return
        direction = get_kwarg(node, "direction")
        if direction is None:
            return  # default 'backward' is point-in-time safe
        value = string_value(direction.value)
        if value not in _FORWARD_DIRECTIONS:
            return

        self._emit(
            node,
            message=(
                f"`merge_asof(..., direction={value!r})` matches each left row to a right row "
                "at or after its timestamp, joining in data from the future. This leaks "
                "information that was not available at the left row's time."
            ),
            fix="Use the point-in-time-safe default: `merge_asof(..., direction='backward')`.",
        )


class LG008(Rule):
    id = "LG008"
    name = "forward-asof-join"
    severity = Severity.ERROR
    short = "merge_asof with direction='forward'/'nearest' joins future rows."
    explanation = (
        "merge_asof aligns two time series by nearest key. With direction='backward' (the "
        "default) each row only sees prior right-side data — point-in-time safe. With "
        "'forward' or 'nearest' it can match a right-side row that occurs later, pulling future "
        "information into the current timestamp and leaking it into the backtest."
    )
    fix_pattern = "pd.merge_asof(left, right, on='ts', direction='backward')"
    visitor_cls = _Visitor
