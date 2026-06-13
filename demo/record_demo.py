"""Fallback demo recorder for environments where VHS can't run.

VHS needs ttyd + ffmpeg, which don't run on native Windows (no ttyd build, no WSL
here). This script reproduces the demo WITHOUT them: it shells out to the real
`leakguard` CLI (so the detection logic is never duplicated — it's the same core
scanner), then renders the captured terminal session straight to an animated GIF with
Pillow. No ttyd, no ffmpeg, no browser.

Usage:
    uv run --extra demo python demo/record_demo.py

If Pillow isn't importable it degrades to printing the real CLI output plus manual
ScreenToGif capture instructions.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET = "demo/strategy_leaky.py"
GIF_PATH = REPO / "demo" / "leakguard_demo.gif"

# Dracula palette.
BG = (40, 42, 54)
FG = (248, 248, 242)
COMMENT = (98, 114, 164)
RED = (255, 85, 85)
GREEN = (80, 250, 123)
YELLOW = (241, 250, 140)
CYAN = (139, 233, 253)

_SGR = {
    "0": ("reset", None),
    "1": ("bold", None),
    "2": ("dim", None),
    "31": ("color", RED),
    "32": ("color", GREEN),
    "33": ("color", YELLOW),
    "36": ("color", CYAN),
}

Cell = tuple  # (char, rgb, is_bullet)
Row = list


def run_cli() -> str:
    """Capture the real CLI output (forced color) — same core scanner, no duplication."""
    proc = subprocess.run(
        [sys.executable, "-m", "leakguard.cli", TARGET, "--color", "always"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


# --- ANSI -> styled characters ---------------------------------------------

def parse_ansi(text: str) -> list[Row]:
    """Each line -> list of (char, rgb, is_bullet). Severity emoji become colored
    bullets so the GIF renders without a color-emoji font."""
    lines: list[Row] = []
    color, dim = FG, False
    current: Row = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\033":  # CSI ... m
            end = text.find("m", i)
            if end != -1:
                for code in text[i + 2 : end].split(";"):
                    kind, val = _SGR.get(code, (None, None))
                    if kind == "reset":
                        color, dim = FG, False
                    elif kind == "dim":
                        dim = True
                    elif kind == "color":
                        color = val
                i = end + 1
                continue
        if ch == "\n":
            lines.append(current)
            current = []
            i += 1
            continue
        if ch in ("🔴", "🟡"):
            current.append(("●", RED if ch == "🔴" else YELLOW, True))
            i += 1
            if i < len(text) and text[i] == "️":  # variation selector
                i += 1
            continue
        if ch in ("️", "‍", "\r"):
            i += 1
            continue
        current.append((ch, COMMENT if dim else color, False))
        i += 1
    lines.append(current)
    return lines


def wrap(line: Row, maxcols: int) -> list[Row]:
    """Wrap a styled line to maxcols, indenting continuations under the text body."""
    if len(line) <= maxcols:
        return [line]
    indent = 0
    while indent < len(line) and line[indent][0] == " ":
        indent += 1
    pad = [(" ", FG, False)] * (indent + 1)
    out: list[Row] = []
    row: Row = []
    for cell in line:
        if len(row) >= maxcols:
            out.append(row)
            row = list(pad)
        row.append(cell)
    if row:
        out.append(row)
    return out


def styled(text: str, color: tuple) -> Row:
    return [(c, color, False) for c in text]


# --- frame script -----------------------------------------------------------

def build_frames(cli_lines: list[Row], maxcols: int) -> list[tuple[list[Row], int]]:
    """Cumulative terminal snapshots: (visible rows, hold ms)."""
    frames: list[tuple[list[Row], int]] = []
    screen: list[Row] = []

    def snap(ms: int) -> None:
        frames.append(([list(r) for r in screen], ms))

    screen.append(styled("# our AI agent wrote a mean-reversion strategy — lint before backtest", COMMENT))
    snap(1100)

    cmd = styled("❯ ", GREEN) + styled("leakguard ", CYAN) + styled(TARGET, FG)
    screen.append([])
    cmd_idx = len(screen) - 1
    for k in range(3, len(cmd), 3):  # typing effect
        screen[cmd_idx] = cmd[:k]
        snap(70)
    screen[cmd_idx] = cmd
    snap(700)

    screen.append([])  # spacing before output
    for ln in cli_lines:
        for w in wrap(ln, maxcols):
            screen.append(w)
        if not ln:  # blank line = end of a finding block → reveal beat
            snap(1500)
    snap(1500)

    screen.append([])
    screen.append(styled("# 3 leaks, each with a one-line fix — the agent self-corrects in one turn", COMMENT))
    snap(1600)
    screen.append(styled("❯ ", GREEN) + styled("echo exit=$?", FG))
    screen.append(styled("1", FG))
    snap(3400)
    return frames


# --- rendering --------------------------------------------------------------

def _load_font(size, ImageFont):
    for path in (
        "C:/Windows/Fonts/CascadiaCode.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render_gif(font_size=18, pad=24, out_path=GIF_PATH, maxcols=96):
    from PIL import Image, ImageDraw, ImageFont

    font = _load_font(font_size, ImageFont)
    cell_w = max(font.getbbox("M")[2], 1)
    ascent, descent = font.getmetrics()
    cell_h = ascent + descent + 4

    cli_lines = parse_ansi(run_cli().rstrip("\n"))
    frames = build_frames(cli_lines, maxcols)

    final_rows = frames[-1][0]
    total_cols = min(max((len(r) for r in final_rows), default=40), maxcols + 4)
    width = pad * 2 + total_cols * cell_w
    height = pad * 2 + len(final_rows) * cell_h

    def render(visible: list[Row]):
        img = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(img)
        for ri, row in enumerate(visible):
            y = pad + ri * cell_h
            for ci, (ch, color, bullet) in enumerate(row):
                x = pad + ci * cell_w
                if bullet:
                    r = cell_w // 2 - 1
                    cx, cy = x + cell_w // 2, y + cell_h // 2
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
                elif ch != " ":
                    draw.text((x, y), ch, font=font, fill=color)
        return img

    images = [render(rows) for rows, _ in frames]
    durations = [ms for _, ms in frames]

    out_path.parent.mkdir(exist_ok=True)
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return out_path, width, height, len(images)


def manual_instructions() -> str:
    return (
        "Manual capture fallback (ScreenToGif):\n"
        "  1. Open a terminal sized ~110x35, Dracula theme.\n"
        f"  2. Run:  uv run leakguard {TARGET}\n"
        "  3. Record the window with ScreenToGif (https://www.screentogif.com),\n"
        "     trim to the command + findings, export as demo/leakguard_demo.gif.\n"
    )


def main() -> int:
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow not installed — run: uv run --extra demo python demo/record_demo.py\n")
        print("Real CLI output (capture this with ScreenToGif):\n")
        sys.stdout.write(run_cli())
        print("\n" + manual_instructions())
        return 0

    path, w, h, nframes = render_gif()
    size_kb = path.stat().st_size / 1024
    print(f"wrote {path}  ({w}x{h}, {nframes} frames, {size_kb:.0f} KB)")
    if size_kb > 3072:
        small = path.with_name("leakguard_demo_small.gif")
        render_gif(font_size=14, pad=16, out_path=small, maxcols=90)
        print(f"wrote {small}  ({small.stat().st_size / 1024:.0f} KB)")
    print("\n" + manual_instructions())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
