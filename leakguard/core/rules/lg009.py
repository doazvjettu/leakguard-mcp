"""LG009 — resample aggregation without right-edge labeling (bar-timestamp leak)."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import receiver_call
from leakguard.core.findings import Severity
from leakguard.core.rules.base import Rule, RuleVisitor, called_method_name, get_kwarg, string_value

# Aggregations applied directly to a resampler that produce one value per bar.
_AGG_METHODS = {"last", "first", "ohlc", "agg", "aggregate", "mean", "sum", "max", "min", "median", "std"}


class _Visitor(RuleVisitor):
    def visit_Call(self, node: cst.Call) -> None:
        if called_method_name(node) not in _AGG_METHODS:
            return
        resampler = receiver_call(node)
        if resampler is None or called_method_name(resampler) != "resample":
            return
        # Safe when the bar is explicitly stamped at its right (close) edge.
        label = get_kwarg(resampler, "label")
        if label is not None and string_value(label.value) == "right":
            return

        self._emit(
            resampler,
            message=(
                "`resample(...)` aggregated without `label='right'` stamps each bar at its left "
                "edge, so the bar's timestamp predates the data it summarizes. Downstream rows "
                "then appear to know the bar's value before it closed — a subtle lookahead leak."
            ),
            fix="Stamp bars at close: `resample(rule, label='right', closed='right')` before aggregating.",
        )


class LG009(Rule):
    id = "LG009"
    name = "resample-label-mismatch"
    severity = Severity.WARNING
    short = "resample().agg without label='right' timestamps bars before their close."
    explanation = (
        "When resampling to coarser bars, the label/closed settings decide which timestamp a "
        "bar carries. With the default left labeling, a bar covering [t, t+Δ) is stamped at t "
        "but aggregates data up to t+Δ — so joining it back by timestamp exposes information "
        "from inside the bar before it finished. Stamping at the right (close) edge keeps the "
        "bar point-in-time honest."
    )
    fix_pattern = "df.resample('1h', label='right', closed='right').last()"
    visitor_cls = _Visitor
