"""Benchmark gates.

The corpus deliberately contains adversarial snippets the scanner is KNOWN to miss
(false negatives) or over-flag (false positives). The gate therefore pins the exact
expected FP/FN sets — a regression is any change to those sets, in either direction:
a new miss is a detection regression; an unexpected disappearance means the corpus
stopped exercising the limitation (or a rule changed silently).
"""

from benchmark.run import (
    GENERAL_CORPUS_DIR,
    GENERAL_LABELS_FILE,
    format_details,
    format_markdown,
    run,
)

# Known limitations, documented in README. (file, rule_id) pairs.
# All corpus false negatives have been resolved by rule fixes:
#   #1 constant propagation — bad_12 (LG001/LG005), bad_14 (LG002)
#   #2 hand-rolled normalization — bad_15 (LG003), gml_bad_07 (LG003)
#   #3 cv=<int> helpers — bad_16 (LG004)
#   #4 drop-based selection — bad_17 (LG005)
# An empty set is a claim, not a victory: it means the CURRENT corpus no longer
# exercises an unhandled miss. New adversarial snippets should repopulate it.
EXPECTED_FN_TRADING: set[tuple[str, str]] = set()
# Resolved by rule fixes and no longer expected over-flags:
#   #5 groupby-chain receiver excluded from LG006 — clean_12
#   #6 expanding/rolling lambdas excluded from LG010 — clean_13
EXPECTED_FP_TRADING = {
    ("clean_06_label_kept_as_target.py", "LG001"),     # forward label, used only as y
    ("clean_09_forward_label_only.py", "LG001"),       # same, pct_change variant
    ("clean_14_helper_function_order.py", "LG003"),    # line order != execution order
    ("clean_15_reporting_resample.py", "LG009"),       # reporting, not features
}
EXPECTED_FN_GENERAL: set[tuple[str, str]] = set()
EXPECTED_FP_GENERAL = {
    ("gml_bad_01_scaler_before_split.py", "LG004"),  # shuffle is fine on non-temporal data
}


def _pairs(detail_list):
    return {(name, rule_id) for name, rule_id, _ in detail_list}


def test_trading_corpus_size_and_floors():
    result = run()
    assert result["n_snippets"] == 39
    assert result["overall"].precision >= 0.84, f"precision regressed: {result['overall'].precision:.2%}"
    assert result["overall"].recall >= 0.84, f"recall regressed: {result['overall'].recall:.2%}"


def test_trading_fp_fn_sets_are_exactly_the_documented_ones():
    result = run()
    assert _pairs(result["false_negatives"]) == EXPECTED_FN_TRADING
    assert _pairs(result["false_positives"]) == EXPECTED_FP_TRADING


def test_general_corpus_size_and_floors():
    result = run(GENERAL_CORPUS_DIR, GENERAL_LABELS_FILE)
    assert result["n_snippets"] == 10
    assert result["overall"].precision >= 0.84
    assert result["overall"].recall >= 0.84


def test_general_fp_fn_sets_are_exactly_the_documented_ones():
    result = run(GENERAL_CORPUS_DIR, GENERAL_LABELS_FILE)
    assert _pairs(result["false_negatives"]) == EXPECTED_FN_GENERAL
    assert _pairs(result["false_positives"]) == EXPECTED_FP_GENERAL


def test_reports_render():
    result = run()
    md = format_markdown(result, title="Trading")
    assert "## Trading" in md and "| **all** |" in md
    details = format_details(result)
    assert "False negatives" in details and "False positives" in details
