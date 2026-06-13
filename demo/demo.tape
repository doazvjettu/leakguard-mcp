# leakguard demo tape — render with:  vhs demo/demo.tape
# (run from the repo root; needs vhs + ttyd + ffmpeg on PATH)

Output demo/leakguard_demo.gif

# VHS Width/Height are PIXELS, not cols/rows. These values target ~110 cols x ~35
# rows at FontSize 13 (≈7.8px/char, ≈15.6px/line, Padding 20). If glyphs look wrong
# on Windows, uncomment one of the FontFamily lines below.
Set FontSize 13
Set Width 1040
Set Height 640
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 80ms
# Set FontFamily "Cascadia Code"
# Set FontFamily "Consolas"

# --- setup (hidden): make `leakguard` resolve via uv, start on a clean screen ---
Hidden
Type "alias leakguard='uv run --quiet leakguard'" Enter
Type "clear" Enter
Show

Sleep 800ms
Type "# Our AI agent just wrote a mean-reversion strategy. Lint it before backtesting:" Enter
Sleep 1200ms

Type "leakguard demo/strategy_leaky.py" Sleep 500ms Enter
Sleep 6500ms

Type "# Three real lookahead leaks — each with a concrete fix the agent can apply." Enter
Sleep 1800ms

Type "# Non-zero exit gates a pre-commit hook or CI:" Enter
Sleep 800ms
Type "echo exit=$?" Enter
Sleep 2500ms
