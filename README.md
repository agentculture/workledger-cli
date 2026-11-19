# workledger-cli

Tracks work in a ledger so agents can prove what they did. An agent records its work as append-only ledger entries, hands the ledger down to subagents, and gets it back with their entries folded in, so the whole tree of work and its results stays traceable and checkable.

The package and distribution are named `workledger-cli`; the command it
installs is `ledger`.

## What is in this repository

- **The `ledger` command** (`workledger/`) — two ledger verbs, `append` and
  `list`, over an append-only JSONL file, plus the self-describing verbs
  `whoami`, `learn`, `explain`, `overview`, `doctor` and `cli overview`. The
  package declares no runtime dependencies.
- **A mesh identity** — `culture.yaml` (`suffix`, `backend: colleague`, `model`)
  and the matching resident prompt file, `AGENTS.colleague.md`.
- **18 skills** under `.claude/skills/`, vendored cite-don't-import. Where each
  one comes from is recorded in [`docs/skill-sources.md`](docs/skill-sources.md).
- **Tests and CI** — `tests/` (pytest), and `.github/workflows/tests.yml`, which
  runs the tests, black, isort, flake8, bandit, markdownlint, the `teken`
  rubric gate, a version-bump check, and SonarCloud. `publish.yml` publishes to
  PyPI and TestPyPI with Trusted Publishing.

## Quickstart

```bash
uv sync
uv run pytest -n auto                 # run the test suite
uv run ledger whoami                  # identity from culture.yaml
uv run ledger learn                   # self-teaching prompt (add --json)
uv run ledger append '{"agent":"a","action":"edit","summary":"did x"}'
uv run ledger list --agent a          # read entries back (add --json)
uv run teken cli doctor . --strict    # the agent-first rubric gate CI runs
```

## CLI

| Verb | What it does |
|------|--------------|
| `whoami` | Report this agent's nick, version, backend, and model from `culture.yaml`. |
| `learn` | Print a structured self-teaching prompt. |
| `explain <path>` | Markdown docs for any noun/verb path. |
| `overview` | Read-only descriptive snapshot of the agent. |
| `doctor` | Check the agent-identity invariants (prompt-file-present, backend-consistency). |
| `append <json>` | Append one entry (`agent`, `action`, `summary`; optional `refs`, `data`) to the append-only ledger (`$WORKLEDGER_PATH` when set; otherwise `.workledger/ledger.jsonl` under the nearest ancestor directory that contains `.git` (else the current directory)). `--stdin` reads JSON from stdin. |
| `list` | Read entries: `--agent`, `--action`, `--since`, `--limit`. |
| `cli overview` | Describe the CLI surface itself. |

Every command supports `--json`. Results go to stdout, errors/diagnostics to
stderr (never mixed). Exit codes: `0` success, `1` user error, `2` environment
error, `3+` reserved.

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
