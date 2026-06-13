"""LG005 — Future-derived target column reused in feature construction (taint)."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import (
    collect_constants,
    contains_future_op,
    subscript_list_keys,
    subscript_string_key,
)
from leakguard.core.findings import Severity
from leakguard.core.rules.base import (
    Rule,
    RuleVisitor,
    called_method_name,
    first_positional,
    get_kwarg,
    string_value,
)


def _string_list(node: cst.BaseExpression) -> list[str] | None:
    """`['a', 'b']` -> ['a', 'b']; `'a'` -> ['a']; anything else -> None."""
    single = string_value(node)
    if single is not None:
        return [single]
    if not isinstance(node, cst.List):
        return None
    out: list[str] = []
    for el in node.elements:
        val = string_value(el.value)
        if val is None:
            return None  # dynamic element — can't reason about what is dropped
        out.append(val)
    return out


def _dropped_columns(call: cst.Call) -> set[str] | None:
    """Column names removed by a `.drop(...)` call, or None if it isn't a
    statically-resolvable column drop (row drops, dynamic lists)."""
    cols = get_kwarg(call, "columns")
    if cols is not None:
        names = _string_list(cols.value)
        return set(names) if names is not None else None
    axis = get_kwarg(call, "axis")
    if axis is not None and (
        (isinstance(axis.value, cst.Integer) and axis.value.value == "1")
        or string_value(axis.value) == "columns"
    ):
        pos = first_positional(call)
        if pos is not None:
            names = _string_list(pos.value)
            return set(names) if names is not None else None
    return None


class _Visitor(RuleVisitor):
    def __init__(self, rule: Rule) -> None:
        super().__init__(rule)
        self._tainted: set[str] = set()  # columns derived from a future op
        self._uses: list[tuple[cst.Subscript, list[str]]] = []  # df[[...]] feature selections
        self._drop_uses: list[tuple[cst.Call, set[str]]] = []  # X = df.drop(columns=[...])

    def visit_Module(self, node: cst.Module) -> None:
        # Constant env so taint sees `shift(H)` with `H = -5` as a future op.
        self._env = collect_constants(node)

    def visit_Assign(self, node: cst.Assign) -> None:
        # df['name'] = <expr containing a future op>  ->  taint 'name'
        if len(node.targets) == 1:
            name = subscript_string_key(node.targets[0].target)
            if name is not None and contains_future_op(node.value, self._env):
                self._tainted.add(name)
                return
        # X = df.drop(columns=[...])  ->  implicit selection of everything NOT dropped.
        # Only assigned drops count: a bare/inplace drop builds no feature matrix.
        value = node.value
        if isinstance(value, cst.Call) and called_method_name(value) == "drop":
            dropped = _dropped_columns(value)
            if dropped is not None:
                self._drop_uses.append((value, dropped))

    def visit_Subscript(self, node: cst.Subscript) -> None:
        keys = subscript_list_keys(node)
        if keys is not None:
            self._uses.append((node, keys))

    def leave_Module(self, original_node: cst.Module) -> None:
        for subscript, keys in self._uses:
            leaked = [k for k in keys if k in self._tainted]
            if not leaked:
                continue
            cols = ", ".join(f"'{c}'" for c in leaked)
            self._emit(
                subscript,
                message=(
                    f"Column(s) {cols} are derived from a future operation (a negative shift/diff) "
                    "yet are selected here as model features. The target's own future information "
                    "flows straight into X — direct label leakage."
                ),
                fix=(
                    "Keep future-derived columns as the prediction target only. Drop them from the "
                    "feature matrix: build X from past-only columns."
                ),
            )
        for call, dropped in self._drop_uses:
            survivors = sorted(self._tainted - dropped)
            if not survivors:
                continue
            cols = ", ".join(f"'{c}'" for c in survivors)
            self._emit(
                call,
                message=(
                    f"The feature matrix is built by dropping columns, but future-derived "
                    f"column(s) {cols} are NOT in the dropped list — the target stays inside X. "
                    "Drop-based selection leaks everything you forget to exclude."
                ),
                fix=(
                    f"Drop the future-derived column(s) too: `df.drop(columns=[..., {cols}])`, "
                    "or select features explicitly with a past-only column list."
                ),
            )


class LG005(Rule):
    id = "LG005"
    name = "label-leakage"
    severity = Severity.ERROR
    short = "A future-derived (negative-shift) column is reused inside the feature matrix."
    explanation = (
        "When a target is built from a future window (e.g. fwd_ret = close.shift(-1)) and that "
        "same column is then included among the features, the model is handed the answer. This "
        "taint rule tracks columns assigned from a future operation and flags any later "
        "selection of them into a feature/X dataframe. Scope is single-file; the target column "
        "must be kept out of the feature set entirely."
    )
    fix_pattern = "y = df['fwd_ret']; X = df[['mom', 'vol']]  # fwd_ret never enters X"
    visitor_cls = _Visitor
