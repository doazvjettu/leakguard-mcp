"""Shared dataflow/structural helpers for the Phase-2 rules (ordering + taint).

Single-file scope only — multi-module taint is explicitly out of scope for v1. These
helpers stay intentionally syntactic: they read column names, list literals, call chains,
and "does this subtree contain a future op", which is all the dataflow we need.
"""

from __future__ import annotations

import libcst as cst

from leakguard.core.rules.base import (
    called_method_name,
    first_positional,
    get_kwarg,
    negative_int_value,
    string_value,
)

FUTURE_METHODS = {"shift", "diff", "pct_change"}

ConstEnv = dict[str, cst.BaseExpression]


def _is_simple_literal(node: cst.BaseExpression) -> bool:
    if isinstance(node, cst.Integer):
        return True
    if isinstance(node, cst.UnaryOperation) and isinstance(node.operator, cst.Minus):
        return isinstance(node.expression, cst.Integer)
    return isinstance(node, cst.Name) and node.value in ("True", "False")


class _ConstantCollector(cst.CSTVisitor):
    """Single-assignment literal constants. Reassignment, augmented assignment, or
    shadowing by a function/lambda parameter poisons the name (dropped from the env) —
    ambiguity must never create a finding."""

    def __init__(self) -> None:
        self.values: ConstEnv = {}
        self._seen: set[str] = set()

    def _bind(self, name: str, value: cst.BaseExpression | None) -> None:
        if name in self._seen:
            self.values.pop(name, None)
            return
        self._seen.add(name)
        if value is not None and _is_simple_literal(value):
            self.values[name] = value

    def visit_Assign(self, node: cst.Assign) -> None:
        for target in node.targets:
            if isinstance(target.target, cst.Name):
                self._bind(target.target.value, node.value)

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if isinstance(node.target, cst.Name):
            self._bind(node.target.value, node.value)

    def visit_AugAssign(self, node: cst.AugAssign) -> None:
        if isinstance(node.target, cst.Name):
            self._bind(node.target.value, None)
            self.values.pop(node.target.value, None)

    def visit_Param(self, node: cst.Param) -> None:
        self._seen.add(node.name.value)
        self.values.pop(node.name.value, None)

    def visit_For(self, node: cst.For) -> None:
        if isinstance(node.target, cst.Name):
            self._seen.add(node.target.value)
            self.values.pop(node.target.value, None)


def collect_constants(module: cst.Module) -> ConstEnv:
    """Simple constant propagation: unambiguous module-wide `NAME = <literal>` bindings."""
    collector = _ConstantCollector()
    module.visit(collector)
    return collector.values


def resolve_constant(node: cst.BaseExpression, env: ConstEnv | None) -> cst.BaseExpression:
    """A Name bound to exactly one literal resolves to that literal; otherwise unchanged."""
    if env and isinstance(node, cst.Name) and node.value in env:
        return env[node.value]
    return node


def is_future_op(node: cst.Call, env: ConstEnv | None = None) -> bool:
    """True for shift/diff/pct_change with a negative `periods` (same shape as LG001)."""
    if called_method_name(node) not in FUTURE_METHODS:
        return False
    arg = get_kwarg(node, "periods") or first_positional(node)
    return arg is not None and negative_int_value(resolve_constant(arg.value, env)) is not None


class _FutureOpFinder(cst.CSTVisitor):
    def __init__(self, env: ConstEnv | None = None) -> None:
        self.found = False
        self._env = env

    def visit_Call(self, node: cst.Call) -> None:
        if is_future_op(node, self._env):
            self.found = True


def contains_future_op(node: cst.CSTNode, env: ConstEnv | None = None) -> bool:
    """True if any future op appears anywhere in this expression subtree."""
    finder = _FutureOpFinder(env)
    node.visit(finder)
    return finder.found


def subscript_string_key(node: cst.BaseExpression) -> str | None:
    """`df['col']` -> 'col'. None if not a single string-key subscript."""
    if not isinstance(node, cst.Subscript) or len(node.slice) != 1:
        return None
    element = node.slice[0].slice
    if isinstance(element, cst.Index):
        return string_value(element.value)
    return None


def subscript_list_keys(node: cst.BaseExpression) -> list[str] | None:
    """`df[['a','b']]` -> ['a','b']. None if not a list-of-strings subscript."""
    if not isinstance(node, cst.Subscript) or len(node.slice) != 1:
        return None
    element = node.slice[0].slice
    if not isinstance(element, cst.Index) or not isinstance(element.value, cst.List):
        return None
    keys: list[str] = []
    for el in element.value.elements:
        val = string_value(el.value)
        if val is not None:
            keys.append(val)
    return keys or None


def chain_calls_method(node: cst.Call, method: str) -> bool:
    """True if `method` is called anywhere in the receiver chain of `node`.

    Walks the receiver spine through Call/Attribute/Subscript, so it sees the groupby in
    both `df.groupby('k').transform(...)` and `df.groupby('k')['c'].transform(...)`.
    """
    current: cst.BaseExpression = node
    while True:
        if isinstance(current, cst.Call):
            if called_method_name(current) == method:
                return True
            current = current.func
        elif isinstance(current, cst.Attribute):
            current = current.value
        elif isinstance(current, cst.Subscript):
            current = current.value
        else:
            return False


# Receiver-name tokens that mark a `.split()` call as a CV splitter, not str.split().
_SPLIT_RECEIVER_HINTS = ("cv", "fold", "tss", "split")


def is_split_call(node: cst.Call) -> bool:
    """True for a train/test split: `train_test_split(...)` (bare or pd-qualified), or
    `<splitter>.split(...)` where the receiver looks like a CV object (cv/kfold/tscv/...).

    Plain string `.split(',')` calls must NOT count — a false split boundary both
    suppresses real LG003/LG010 findings and creates spurious ones.
    """
    name = called_method_name(node, allow_bare=True)
    if name == "train_test_split":
        return True
    if name != "split" or not isinstance(node.func, cst.Attribute):
        return False
    receiver = " ".join(names_in(node.func.value)).lower()
    return any(hint in receiver for hint in _SPLIT_RECEIVER_HINTS)


def receiver_call(node: cst.Call) -> cst.Call | None:
    """The immediate receiver if it is itself a call: `a.b().c()` -> the `a.b()` call."""
    func = node.func
    if isinstance(func, cst.Attribute) and isinstance(func.value, cst.Call):
        return func.value
    return None


class _NameCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.names: list[str] = []

    def visit_Name(self, node: cst.Name) -> None:
        self.names.append(node.value)


def names_in(node: cst.CSTNode) -> list[str]:
    """All identifier names appearing in a subtree (used for crude estimator typing)."""
    collector = _NameCollector()
    node.visit(collector)
    return collector.names
