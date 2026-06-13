"""leakguard CLI — a thin terminal front-end over the pure core scanner.

Wraps `LeakGuard.scan()`; contains zero detection logic. Exists so humans (and demos)
get readable, colored findings without speaking the MCP protocol.

    leakguard path/to/strategy.py
    leakguard lint-file path/to/strategy.py --no-color
"""

from __future__ import annotations

import argparse
import os
import sys

from leakguard.core import LeakGuard, Severity

# --- ANSI styling -----------------------------------------------------------

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"

_SEV_ICON = {Severity.ERROR: "🔴", Severity.WARNING: "🟡"}
_SEV_COLOR = {Severity.ERROR: _RED, Severity.WARNING: _YELLOW}


class _Style:
    """Color helpers that collapse to no-ops when color is disabled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if self.enabled else text

    def bold(self, t: str) -> str:
        return self._wrap(_BOLD, t)

    def dim(self, t: str) -> str:
        return self._wrap(_DIM, t)

    def red(self, t: str) -> str:
        return self._wrap(_RED, t)

    def green(self, t: str) -> str:
        return self._wrap(_GREEN, t)

    def cyan(self, t: str) -> str:
        return self._wrap(_CYAN, t)

    def sev(self, severity: Severity, t: str) -> str:
        return self._wrap(_SEV_COLOR.get(severity, ""), t)


def _want_color(flag: str) -> bool:
    if flag == "always":
        return True
    if flag == "never" or os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _render(findings, filename: str, style: _Style) -> str:
    lines: list[str] = []
    lines.append(style.cyan(f"leakguard  {filename}"))
    lines.append("")

    if not findings:
        lines.append(style.green("✓ no leakage patterns found"))
        return "\n".join(lines)

    for f in findings:
        severity = f.severity
        icon = _SEV_ICON.get(severity, "•")
        head = (
            f"{icon} {style.bold(style.sev(severity, f.rule_id))} "
            f"{style.dim(f'line {f.line}:{f.col}')}  "
            f"{style.sev(severity, severity.value)}"
        )
        lines.append(head)
        lines.append(f"   {f.message}")
        lines.append(f"   {style.dim('fix:')} {style.green(f.fix)}")
        lines.append("")

    n_err = sum(1 for f in findings if f.severity is Severity.ERROR)
    n_warn = sum(1 for f in findings if f.severity is Severity.WARNING)
    summary = f"{len(findings)} finding(s): {n_err} error, {n_warn} warning"
    lines.append(style.bold(summary))
    return "\n".join(lines)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    # Accept an optional `lint-file` verb so both invocation styles work.
    if argv and argv[0] == "lint-file":
        argv = argv[1:]
    parser = argparse.ArgumentParser(
        prog="leakguard", description="Static leakage / lookahead-bias scanner."
    )
    parser.add_argument("path", help="Python file to scan")
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="colorize output (default: auto)",
    )
    parser.add_argument("--no-color", action="store_const", const="never", dest="color")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))
    style = _Style(_want_color(args.color))

    try:
        with open(args.path, "r", encoding="utf-8") as fh:
            code = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(style.red(f"error: cannot read {args.path}: {exc}"), file=sys.stderr)
        return 2

    result = LeakGuard().scan_result(code, filename=args.path)
    if not result.ok:
        print(style.red(f"parse error in {args.path}: {result.parse_error}"), file=sys.stderr)
        return 2

    print(_render(result.findings, args.path, style))
    # Exit non-zero when leakage is found, so it can gate a pre-commit hook / CI.
    return 1 if result.findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
