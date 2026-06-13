"""LG010 — groupby transform/agg computed on the full frame before the split."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import chain_calls_method, is_split_call
from leakguard.core.findings import Severity
from leakguard.core.rules.base import Rule, RuleVisitor, called_method_name, first_positional

_AGG_METHODS = {"transform", "agg", "aggregate"}

# Window builders that only ever see past rows — a lambda built on them is
# point-in-time safe even when computed over the full frame.
_PIT_WINDOWS = {"expanding", "rolling"}


class _PITWindowFinder(cst.CSTVisitor):
    def __init__(self) -> None:
        self.found = False

    def visit_Call(self, node: cst.Call) -> None:
        if called_method_name(node) in _PIT_WINDOWS:
            self.found = True


def _is_pit_safe_lambda(call: cst.Call) -> bool:
    """True for `transform(lambda s: s.expanding()...)` / `...s.rolling(n)...` —
    the group statistic at each row only uses that row's past."""
    arg = first_positional(call)
    if arg is None or not isinstance(arg.value, cst.Lambda):
        return False
    finder = _PITWindowFinder()
    arg.value.body.visit(finder)
    return finder.found


class _Visitor(RuleVisitor):
    def __init__(self, rule: Rule) -> None:
        super().__init__(rule)
        self._group_aggs: list[cst.Call] = []
        self._split_lines: list[int] = []

    def visit_Call(self, node: cst.Call) -> None:
        method = called_method_name(node)
        if method in _AGG_METHODS and chain_calls_method(node, "groupby"):
            if not _is_pit_safe_lambda(node):
                self._group_aggs.append(node)
        elif is_split_call(node):
            self._split_lines.append(self._line(node))

    def leave_Module(self, original_node: cst.Module) -> None:
        if not self._split_lines:
            return
        first_split = min(self._split_lines)
        for agg in self._group_aggs:
            if self._line(agg) < first_split:
                self._emit(
                    agg,
                    message=(
                        "A `groupby(...).transform()/agg()` is computed over the full frame here, "
                        "then the data is split later. The group statistic mixes train and test "
                        "rows (and future with past within each group), leaking across the split "
                        "boundary."
                    ),
                    fix=(
                        "Compute group aggregates after splitting, fitted on train only — or use an "
                        "expanding/rolling groupby so each row only sees prior rows in its group."
                    ),
                )


class LG010(Rule):
    id = "LG010"
    name = "groupby-across-split"
    severity = Severity.WARNING
    short = "groupby().transform()/agg() on the full df before the train/test split."
    explanation = (
        "A group-wise transform or aggregate over the whole dataframe summarizes every row in "
        "each group, future and test rows included. Splitting afterwards leaves those leaked "
        "group statistics inside the training features. This is the groupby generalization of "
        "LG003: the aggregate must be fitted on the training partition (or made expanding) so it "
        "never sees data from the other side of the split."
    )
    fix_pattern = "train, test = split(df); g = train.groupby('sym')['x'].transform('mean')"
    visitor_cls = _Visitor
