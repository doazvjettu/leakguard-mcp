# Publishing & directory listings

Runbook for releasing `leakguard-mcp` to PyPI and listing it on MCP directories.

## Status

- **PyPI:** published — `pip install leakguard-mcp` (v0.1.0).
- **Repo manifests:** `server.json` (official registry) and `smithery.yaml` (Smithery)
  live in the repo root.

---

## 1. PyPI release

### Manual (what we used)
```bash
uv build                      # -> dist/*.whl + *.tar.gz
uvx twine check dist/*        # validate metadata
uv publish                    # uses $UV_PUBLISH_TOKEN, ~/.pypirc, or --token
```

**Do not paste the token on the command line** (it lands in shell history / logs).
Use an environment variable in your own shell instead:
```bash
export UV_PUBLISH_TOKEN=pypi-…
uv publish
```

### Bump a version
1. Edit `version` in `pyproject.toml`.
2. Update `version` in `server.json` (keep it in sync).
3. `uv build && uv publish`.
4. Tag it: `git tag v0.1.0 && git push --tags`, then cut a GitHub Release.

---

## 2. CI auto-publish — use Trusted Publishing, NOT a stored token

**You do not need a PyPI token in GitHub Secrets.** A long-lived token in Secrets is a
standing leak risk. PyPI Trusted Publishing (OIDC) lets a GitHub Actions workflow publish
with no secret at all.

One-time setup on PyPI: project → *Settings* → *Publishing* → add a GitHub trusted
publisher (owner `doazvjettu`, repo `leakguard-mcp`, workflow `release.yml`,
environment `pypi`).

Then a tag-triggered workflow (`.github/workflows/release.yml`):
```yaml
name: release
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write          # OIDC — this is what replaces the token
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv build
      - run: uv publish          # no token needed; OIDC handles auth
```

---

## 3. Official MCP registry

`server.json` is ready (`io.github.doazvjettu/leakguard-mcp`). Install the publisher CLI
from <https://github.com/modelcontextprotocol/registry>, then:
```bash
mcp-publisher login github     # OAuth; verifies the io.github.doazvjettu/* namespace
mcp-publisher publish          # reads ./server.json
```
Note: opening a PR against `modelcontextprotocol/servers` is the *old* path. The current
registry uses `mcp-publisher`.

---

## 4. Smithery

`smithery.yaml` (stdio local) is ready. At <https://smithery.ai> → *Add Server* → sign in
with GitHub → pick `leakguard-mcp`. Smithery reads the YAML and builds it.

---

## 5. glama.ai

glama auto-crawls public GitHub MCP servers, so the listing usually appears on its own.
To help/claim it: sign in at <https://glama.ai>, and on the GitHub repo add the topics
`mcp`, `mcp-server`, `model-context-protocol` plus an "About" description.

---

## 6. mcpmarket.com

Submit via the form at <https://mcpmarket.com> (GitHub sign-in): repo URL, install command
`pip install leakguard-mcp`, and the MCP config block from the README.

---

## Suggested order

PyPI → registry → Smithery → glama → mcpmarket. Every directory points back at the PyPI
package, so publish that first (done).

## Security

- Never paste a PyPI token into a prompt, command line, or committed file.
- Prefer Trusted Publishing (section 2) over a stored token.
- If a token is ever exposed, revoke it at <https://pypi.org/manage/account/token/>
  immediately and mint a new project-scoped one.
