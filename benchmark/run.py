"""Benchmark runner — per-rule precision/recall against labeled corpora, two tiers.

Tiers
-----
1. Trading-specific corpus (`benchmark/corpus/`): author-written snippets modeled on
   real bug shapes from trading-strategy development. The same author wrote the rules,
   so treat these numbers as REGRESSION FIXTURES, not independent validation.
2. General-ML corpus (`benchmark/corpus_general/`): author-composed reproductions of
   leakage anti-patterns that are widely documented in the ML-leakage literature
   (preprocessing-before-split, target leakage via aggregation, shuffled CV on ordered
   data). Honest provenance: NO public dataset is bundled or downloaded — these are
   reconstructions of known patterns, one arm's length removed in domain, not in
   authorship.

Labels (`labels.json` / `labels_general.json`) are GROUND TRUTH leak instances per
file — `{filename: {rule_id: count}}` — not expected tool output. Where the scanner
disagrees with ground truth, that shows up as a false positive or false negative, and
this runner prints both lists explicitly instead of hiding them in an aggregate.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from leakguard.core import RULES, LeakGuard

CORPUS_DIR = Path(__file__).parent / "corpus"
LABELS_FILE = Path(__file__).parent / "labels.json"
GENERAL_CORPUS_DIR = Path(__file__).parent / "corpus_general"
GENERAL_LABELS_FILE = Path(__file__).parent / "labels_general.json"

TIERS = [
    ("Trading-specific corpus", CORPUS_DIR, LABELS_FILE),
    ("General-ML corpus", GENERAL_CORPUS_DIR, GENERAL_LABELS_FILE),
]


@dataclass
class Score:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def add(self, other: "Score") -> None:
        self.tp += other.tp
        self.fp += other.fp
        self.fn += other.fn

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 1.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def score_file(detected: Counter, expected: dict[str, int]) -> dict[str, Score]:
    """Per-rule TP/FP/FN for one snippet (instance-level via expected counts)."""
    out: dict[str, Score] = {}
    for rule_id in set(detected) | set(expected):
        det, exp = detected.get(rule_id, 0), expected.get(rule_id, 0)
        out[rule_id] = Score(tp=min(det, exp), fp=max(0, det - exp), fn=max(0, exp - det))
    return out


def run(corpus_dir: Path = CORPUS_DIR, labels_file: Path = LABELS_FILE) -> dict:
    """Scan one labeled corpus. Returns per-rule/overall Scores plus explicit
    false-positive and false-negative detail lists [(file, rule_id, count)]."""
    labels = json.loads(labels_file.read_text(encoding="utf-8"))
    guard = LeakGuard()  # full ruleset, ungated

    per_rule: dict[str, Score] = {r.id: Score() for r in RULES}
    overall = Score()
    false_positives: list[tuple[str, str, int]] = []
    false_negatives: list[tuple[str, str, int]] = []

    for name in sorted(labels):
        expected = labels[name]
        code = (corpus_dir / name).read_text(encoding="utf-8")
        detected = Counter(f.rule_id for f in guard.scan(code, filename=name))
        for rule_id, sc in sorted(score_file(detected, expected).items()):
            per_rule.setdefault(rule_id, Score()).add(sc)
            overall.add(sc)
            if sc.fp:
                false_positives.append((name, rule_id, sc.fp))
            if sc.fn:
                false_negatives.append((name, rule_id, sc.fn))

    return {
        "per_rule": per_rule,
        "overall": overall,
        "n_snippets": len(labels),
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def format_markdown(result: dict, title: str | None = None) -> str:
    lines = []
    if title:
        lines.append(f"## {title}")
    lines += [
        f"Corpus: {result['n_snippets']} labeled snippets.",
        "",
        "| Rule | Precision | Recall | F1 | TP | FP | FN |",
        "|------|-----------|--------|----|----|----|----|",
    ]
    for rule_id in sorted(result["per_rule"]):
        s = result["per_rule"][rule_id]
        if s.tp == s.fp == s.fn == 0:
            continue
        lines.append(
            f"| {rule_id} | {s.precision:.0%} | {s.recall:.0%} | {s.f1:.2f} | {s.tp} | {s.fp} | {s.fn} |"
        )
    o = result["overall"]
    lines.append(
        f"| **all** | **{o.precision:.0%}** | **{o.recall:.0%}** | **{o.f1:.2f}** | {o.tp} | {o.fp} | {o.fn} |"
    )
    return "\n".join(lines)


def format_details(result: dict) -> str:
    """Explicit FP/FN lists — the honest part. Never hide the misses."""
    lines = []
    fns = result["false_negatives"]
    fps = result["false_positives"]
    lines.append(f"False negatives (labeled leaks the scanner MISSED): {sum(n for _, _, n in fns)}")
    for name, rule_id, n in fns:
        lines.append(f"  - {name}: {rule_id} x{n}")
    if not fns:
        lines.append("  (none)")
    lines.append(f"False positives (clean code the scanner flagged): {sum(n for _, _, n in fps)}")
    for name, rule_id, n in fps:
        lines.append(f"  - {name}: {rule_id} x{n}")
    if not fps:
        lines.append("  (none)")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the leakguard benchmark corpora.")
    parser.add_argument("--corpus", type=Path, default=None, help="single-corpus mode")
    parser.add_argument("--labels", type=Path, default=None, help="single-corpus mode")
    args = parser.parse_args()

    if args.corpus or args.labels:
        result = run(args.corpus or CORPUS_DIR, args.labels or LABELS_FILE)
        print(format_markdown(result))
        print()
        print(format_details(result))
        return

    combined = Score()
    combined_n = 0
    for title, corpus_dir, labels_file in TIERS:
        result = run(corpus_dir, labels_file)
        print(format_markdown(result, title=title))
        print()
        print(format_details(result))
        print()
        combined.add(result["overall"])
        combined_n += result["n_snippets"]

    print("## Combined")
    print(
        f"{combined_n} snippets | precision {combined.precision:.1%} | "
        f"recall {combined.recall:.1%} | F1 {combined.f1:.2f} "
        f"(TP {combined.tp} / FP {combined.fp} / FN {combined.fn})"
    )


if __name__ == "__main__":
    main()
