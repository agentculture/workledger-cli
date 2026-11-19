"""Markdown catalog for ``ledger explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple,
``("workledger-cli",)`` and ``("ledger",)`` all resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

from workledger._about import COMMAND, DISTRIBUTION, summary
from workledger.cli._commands._store import DEFAULT_LOCATION_RULE, ENV_PATH

_ROOT = f"""\
# {DISTRIBUTION} (command: `{COMMAND}`)

{summary()} An agent records each piece of work as one entry in an append-only
ledger (`append`) and reads entries back with filters (`list`). There is no
edit, update, or delete verb, so the record stays traceable and checkable.
Agents and subagents that are given the same ledger file add their entries to
the one record.

The ledger is a JSONL file: `${ENV_PATH}` when that is set; otherwise
{DEFAULT_LOCATION_RULE}.

The package is `{DISTRIBUTION}`; the command it installs is `{COMMAND}`.

## Verbs

- `ledger whoami` — identity probe from `culture.yaml`.
- `ledger learn` — structured self-teaching prompt.
- `ledger explain <path>` — markdown docs for any noun/verb.
- `ledger overview` — descriptive snapshot of the agent.
- `ledger doctor` — check the agent-identity invariants.
- `ledger append <json>` — append one entry to the ledger.
- `ledger list` — read ledger entries with filters.
- `ledger cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `ledger explain append`
- `ledger explain list`
- `ledger explain whoami`
- `ledger explain doctor`
"""

_WHOAMI = """\
# ledger whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    ledger whoami
    ledger whoami --json
"""

_LEARN = """\
# ledger learn

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    ledger learn
    ledger learn --json
"""

_EXPLAIN = """\
# ledger explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    ledger explain ledger
    ledger explain whoami
    ledger explain --json <path>
"""

_OVERVIEW = """\
# ledger overview

Read-only descriptive snapshot of the agent, in four sections: identity (from
`culture.yaml`), the verb surface, the artifacts the repository carries, and
what the package is for. Accepts an ignored `target` so a stray path never
hard-fails.

## Usage

    ledger overview
    ledger overview --json
"""

_DOCTOR = """\
# ledger doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`colleague` → `AGENTS.colleague.md`), plus a
skills-present check. Exits 1 when unhealthy.

## Usage

    ledger doctor
    ledger doctor --json
"""

_CLI = """\
# ledger cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    ledger cli overview
    ledger cli overview --json
"""


_APPEND = f"""\
# ledger append

Appends exactly one entry to the append-only ledger and prints the stored entry
(with generated `id` and UTC `timestamp`). This is the only write verb; there is
no edit, update, or delete.

Required fields: `agent`, `action`, `summary` (non-empty strings). Optional:
`refs` (list of strings), `data` (JSON object). `id` and `timestamp` are
generated and rejected if supplied; unknown fields are rejected (exit 1).

Storage: a JSONL file. `${ENV_PATH}`, when set, is used as given (a relative
value is relative to the current directory). Otherwise the file is
{DEFAULT_LOCATION_RULE}.
The search starts at the current directory itself, and `.git` may be a
directory or a file (worktrees, submodules).

## Usage

    ledger append '{{"agent":"a","action":"edit","summary":"did x"}}' --json
    echo '{{"agent":"a","action":"edit","summary":"did x"}}' | ledger append --stdin
"""

_LIST = """\
# ledger list

Lists ledger entries oldest first. Filters combine with AND: `--agent NAME`,
`--action NAME`, `--since ISO8601` (inclusive; naive means UTC), `--limit N`
(the most recent N matches). `--json` emits an array; a missing ledger is an
empty array.

## Usage

    ledger list
    ledger list --agent a --since 2026-01-01T00:00:00Z --limit 5 --json
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
