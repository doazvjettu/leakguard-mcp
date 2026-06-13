"""Rule base + shared libcst matcher helpers.

A Rule is a stateless descriptor (id/name/severity/docs) plus a visitor factory. The
visitor walks one parsed module and appends Findings. Helpers below centralize the
fiddly libcst node-shape checks so individual rules stay declarative.
"""

from __future__ import annotations

import libcst as cst
from libcst.metadata import PositionProvider

from leakguard.core.findings import Finding, Severity


# --- libcst matcher helpers -------------------------------------------------

def called_method_name(node: cst.Call, allow_bare: bool = False) -> str | None:
    """Return the method name for `<obj>.<method>(...)`, else None.

    `allow_bare=True` also matches plain `name(...)` calls, for APIs commonly imported
    directly (`merge_asof`, `train_test_split`, `KFold`). Off by default so method-shaped
    rules (shift/bfill/rolling) don't fire on user functions that share the name.
    """
    func = node.func
    if isinstance(func, cst.Attribute):
        return func.attr.value
    if allow_bare and isinstance(func, cst.Name):
        return func.value
    return None


def positional_args(node: cst.Call) -> list[cst.Arg]:
    """Positional (non-keyword, non-star) arguments, in order."""
    return [a for a in node.args if a.keyword is None and a.star == ""]


def get_kwarg(node: cst.Call, name: str) -> cst.Arg | None:
    """Find a keyword argument by name."""
    for arg in node.args:
        if arg.keyword is not None and arg.keyword.value == name:
            return arg
    return None


def first_positional(node: cst.Call) -> cst.Arg | None:
    """First positional (non-keyword, non-star) argument, if any."""
    for arg in node.args:
        if arg.keyword is None and arg.star == "":
            return arg
    return None


def is_true_literal(node: cst.BaseExpression) -> bool:
    return isinstance(node, cst.Name) and node.value == "True"


def string_value(node: cst.BaseExpression) -> str | None:
    """Extract a plain string literal's value, else None (ignores f-strings/concats)."""
    if isinstance(node, cst.SimpleString):
        return node.evaluated_value
    return None


def negative_int_value(node: cst.BaseExpression) -> int | None:
    """Return n for a literal `-n` (n a positive int), else None.

    Detects the unary-minus wrapper libcst uses for negative literals; a bare positive
    Integer returns None (positive shifts are safe / backward-looking).
    """
    if isinstance(node, cst.UnaryOperation) and isinstance(node.operator, cst.Minus):
        inner = node.expression
        if isinstance(inner, cst.Integer):
            return int(inner.evaluated_value)
    return None


# --- rule + visitor base ----------------------------------------------------

class RuleVisitor(cst.CSTVisitor):
    """Base visitor: carries the owning rule and collects Findings with positions."""

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, rule: "Rule") -> None:
        super().__init__()
        self.rule = rule
        self.findings: list[Finding] = []

    def _line(self, node: cst.CSTNode) -> int:
        return self.get_metadata(PositionProvider, node).start.line

    def _emit(self, node: cst.CSTNode, message: str, fix: str) -> None:
        pos = self.get_metadata(PositionProvider, node)
        self.findings.append(
            Finding(
                rule_id=self.rule.id,
                name=self.rule.name,
                severity=self.rule.severity,
                line=pos.start.line,
                col=pos.start.column,
                message=message,
                fix=fix,
            )
        )


class Rule:
    """Static rule descriptor. Subclasses set the class attrs and `visitor_cls`."""

    id: str
    name: str
    severity: Severity
    short: str  # one-line summary for list_rules()
    explanation: str  # long-form rationale for explain_rule()
    fix_pattern: str  # canonical fix snippet for explain_rule()
    visitor_cls: type[RuleVisitor]

    def visitor(self) -> RuleVisitor:
        return self.visitor_cls(self)

    def catalog_entry(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "short": self.short,
        }
