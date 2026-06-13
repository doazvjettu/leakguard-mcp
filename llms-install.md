# Installing leakguard-mcp (for AI install agents)

leakguard-mcp is a local **stdio** MCP server. No API keys, no environment variables, no
network access — it statically analyzes Python source for data-leakage / lookahead-bias.

## Steps

1. Install the package (Python 3.11+):
   ```bash
   pip install leakguard-mcp
   ```
   (or `uv pip install leakguard-mcp`)

2. Add the server to the MCP settings file:
   ```json
   {
     "mcpServers": {
       "leakguard": {
         "command": "python",
         "args": ["-m", "leakguard.server"]
       }
     }
   }
   ```
   On systems where `python` is not the 3.11+ interpreter, use the full path or `python3`.

3. No configuration is required. There are no secrets or env vars to set.

## Verify

After the server starts, the agent should see these tools:
`lint_code`, `lint_file`, `lint_paths`, `list_rules`, `explain_rule`.

Quick check — `lint_code` on a known-leaky snippet returns a finding:
```
lint_code(code="df['x'] = df['close'].shift(-1)")
# -> {"ok": true, "parse_error": null,
#     "findings": [{"rule_id": "LG001", "severity": "error", ...}]}
```

A non-empty `findings` array (rule `LG001`) confirms the server is working.
