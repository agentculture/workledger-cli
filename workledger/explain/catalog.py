"""Markdown catalog for ``workledger-cli explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
and ``("workledger-cli",)`` both resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# workledger-cli

A clonable template for AgentCulture mesh agents. It carries an agent-first CLI
(cited from the teken `python-cli` reference), a mesh identity (`culture.yaml` +
`CLAUDE.md`), the canonical guildmaster skill kit under `.claude/skills/`, and a
buildable/deployable package baseline. Clone it, rename the package, edit
`culture.yaml`, and you have a new agent.

## Verbs

- `workledger-cli whoami` — identity probe from `culture.yaml`.
- `workledger-cli learn` — structured self-teaching prompt.
- `workledger-cli explain <path>` — markdown docs for any noun/verb.
- `workledger-cli overview` — descriptive snapshot of the agent.
- `workledger-cli doctor` — check the agent-identity invariants.
- `workledger-cli append <json>` — append one entry to the ledger.
- `workledger-cli list` — read ledger entries with filters.
- `workledger-cli cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `workledger-cli explain whoami`
- `workledger-cli explain doctor`
"""

_WHOAMI = """\
# workledger-cli whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    workledger-cli whoami
    workledger-cli whoami --json
"""

_LEARN = """\
# workledger-cli learn

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    workledger-cli learn
    workledger-cli learn --json
"""

_EXPLAIN = """\
# workledger-cli explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    workledger-cli explain workledger-cli
    workledger-cli explain whoami
    workledger-cli explain --json <path>
"""

_OVERVIEW = """\
# workledger-cli overview

Read-only descriptive snapshot of the agent: identity (from `culture.yaml`), the
verb surface, and the sibling-pattern artifacts the template carries. Accepts an
ignored `target` so a stray path never hard-fails.

## Usage

    workledger-cli overview
    workledger-cli overview --json
"""

_DOCTOR = """\
# workledger-cli doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`colleague` → `AGENTS.colleague.md`), plus a
skills-present check. Exits 1 when unhealthy.

## Usage

    workledger-cli doctor
    workledger-cli doctor --json
"""

_CLI = """\
# workledger-cli cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    workledger-cli cli overview
    workledger-cli cli overview --json
"""


_APPEND = """\
# workledger-cli append

Appends exactly one entry to the append-only ledger and prints the stored entry
(with generated `id` and UTC `timestamp`). This is the only write verb; there is
no edit, update, or delete.

Required fields: `agent`, `action`, `summary` (non-empty strings). Optional:
`refs` (list of strings), `data` (JSON object). `id` and `timestamp` are
generated and rejected if supplied; unknown fields are rejected (exit 1).

Storage: JSONL at `$WORKLEDGER_PATH`, default `./.workledger/ledger.jsonl`.

## Usage

    workledger-cli append '{"agent":"a","action":"edit","summary":"did x"}' --json
    echo '{"agent":"a","action":"edit","summary":"did x"}' | workledger-cli append --stdin
"""

_LIST = """\
# workledger-cli list

Lists ledger entries oldest first. Filters combine with AND: `--agent NAME`,
`--action NAME`, `--since ISO8601` (inclusive; naive means UTC), `--limit N`
(the most recent N matches). `--json` emits an array; a missing ledger is an
empty array.

## Usage

    workledger-cli list
    workledger-cli list --agent a --since 2026-01-01T00:00:00Z --limit 5 --json
"""

ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("workledger-cli",): _ROOT,
    ("ledger",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("doctor",): _DOCTOR,
    ("append",): _APPEND,
    ("list",): _LIST,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
}
