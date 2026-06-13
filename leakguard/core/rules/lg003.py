"""LG003 — Scaler/transformer fitted on the full frame before the train/test split."""

from __future__ import annotations

import libcst as cst

from leakguard.core.dataflow import is_split_call, names_in
from leakguard.core.findings import Severity
from leakguard.core.rules.base import Rule, RuleVisitor, called_method_name, positional_args

# Identifiers that mark the receiver as a preprocessing transformer (not an estimator).
_TRANSFORMER_HINTS = ("scaler", "scale", "normaliz", "standardiz", "encoder", "imputer", "pca", "transformer")

# Whole-frame reductions used in hand-rolled normalization (z-score, min-max).
_FRAME_STATS = {"mean", "std", "min", "max"}


def _is_frame_stat_call(node: cst.BaseExpression) -> bool:
    """`X.mean()` / `X.std()` / `X.min()` / `X.max()` — argument-free reduction on a
    bare-Name frame. Windowed (`x.rolling(...).mean()`) or column (`df['c'].mean()`)
    receivers don't qualify; those are LG006's territory or already point-in-time safe."""
    if not isinstance(node, cst.Call) or node.args:
        return False
    func = node.func
    return (
        isinstance(func, cst.Attribute)
        and func.attr.value in _FRAME_STATS
        and isinstance(func.value, cst.Name)
    )


class _StatUsageFinder(cst.CSTVisitor):
    """Finds a frame-stat call or a variable holding one inside an expression."""

    def __init__(self, stat_vars: set[str]) -> None:
        self._stat_vars = stat_vars
        self.found = False

    def visit_Call(self, node: cst.Call) -> None:
        if _is_frame_stat_call(node):
            self.found = True

    def visit_Name(self, node: cst.Name) -> None:
        if node.value in self._stat_vars:
            self.found = True


def _looks_like_transformer(node: cst.Call) -> bool:
    func = node.func
    if not isinstance(func, cst.Attribute):
        return False
    receiver_names = " ".join(names_in(func.value)).lower()
    return any(hint in receiver_names for hint in _TRANSFORMER_HINTS)


def _is_transformer_fit(node: cst.Call) -> bool:
    """Distinguish a preprocessing `.fit(X)` from an estimator `.fit(X, y)`.

    Transformers fit on features alone (one argument); estimators take X and y. A
    scaler-like receiver name also qualifies regardless of arity.
    """
    if not isinstance(node.func, cst.Attribute):
        return False
    return _looks_like_transformer(node) or len(positional_args(node)) == 1


class _Visitor(RuleVisitor):
    def __init__(self, rule: Rule) -> None:
        super().__init__(rule)
        self._fits: list[cst.Call] = []
        self._split_lines: list[int] = []
        self._stat_vars: set[str] = set()
        self._norm_assigns: list[cst.Assign] = []

    def visit_Call(self, node: cst.Call) -> None:
        method = called_method_name(node)
        if method == "fit_transform" or (method == "fit" and _is_transformer_fit(node)):
            self._fits.append(node)
        elif is_split_call(node):
            self._split_lines.append(self._line(node))

    def visit_Assign(self, node: cst.Assign) -> None:
        # `mu = X.mean()` → remember the variable holding a whole-frame statistic.
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0].target, cst.Name)
            and _is_frame_stat_call(node.value)
        ):
            self._stat_vars.add(node.targets[0].target.value)
            return
        # `X_z = (X - mu) / sigma` / `(X - X.min()) / (X.max() - X.min())` — an
        # arithmetic expression mixing the data with a whole-frame statistic.
        # Top-level BinaryOperation only: keeps stats nested in lambdas/calls
        # (groupby zscores — LG010's territory) out of this branch.
        if isinstance(node.value, cst.BinaryOperation):
            finder = _StatUsageFinder(self._stat_vars)
            node.value.visit(finder)
            if finder.found:
                self._norm_assigns.append(node)

    def leave_Module(self, original_node: cst.Module) -> None:
        if not self._split_lines:
            return  # no split in this file → can't assert ordering
        first_split = min(self._split_lines)
        for fit in self._fits:
            if self._line(fit) < first_split:
                self._emit(
                    fit,
                    message=(
                        "A scaler/transformer is fitted on the full dataset on this line, but the "
                        "train/test split happens later. The fitted statistics (mean, std, min/max, "
                        "encoding) absorb information from the test rows, leaking it into training."
                    ),
                    fix=(
                        "Split first, then `fit` on train only and `transform` test: "
                        "`scaler.fit(X_train); X_test = scaler.transform(X_test)` "
                        "(or wrap in a Pipeline inside cross-validation)."
                    ),
                )
        for assign in self._norm_assigns:
            if self._line(assign) < first_split:
                self._emit(
                    assign,
                    message=(
                        "This expression normalizes the data with a whole-frame statistic "
                        "(mean/std/min/max computed over ALL rows), and the train/test split only "
                        "happens later. The statistic already contains the test rows — the same "
                        "leak as fitting a scaler before the split, just hand-rolled."
                    ),
                    fix=(
                        "Split first and compute the statistics on the train partition only: "
                        "`mu = X_train.mean(); sd = X_train.std(); X_test_z = (X_test - mu) / sd`."
                    ),
                )


class LG003(Rule):
    id = "LG003"
    name = "global-fit-scaling"
    severity = Severity.ERROR
    short = "Scaler/transformer fit() or fit_transform() before the train/test split."
    explanation = (
        "Fitting a scaler, encoder, imputer or PCA on the whole dataset lets its parameters "
        "(mean/std, min/max, category set, components) see the test data. When you split "
        "afterwards, those leaked statistics are already baked into the training transform, "
        "inflating backtest performance. The fit must happen on the training partition only — "
        "typically via a Pipeline evaluated inside the cross-validator."
    )
    fix_pattern = "X_train, X_test = split(...); scaler.fit(X_train); scaler.transform(X_test)"
    visitor_cls = _Visitor
