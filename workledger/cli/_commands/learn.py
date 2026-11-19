"""``ledger learn`` — the learnability affordance.

Prints a structured self-teaching prompt. Must satisfy the agent-first rubric:
>=200 chars and mention purpose, command map, exit codes, --json, and explain.
"""

from __future__ import annotations

import argparse

from workledger import __version__
from workledger._about import COMMAND, DISTRIBUTION, summary
from workledger.cli._commands._store import DEFAULT_LOCATION_RULE, ENV_PATH
from workledger.cli._output import emit_result

_TEXT = f"""\
{DISTRIBUTION} (command: `{COMMAND}`)

{summary()}

Purpose
-------
A work ledger for agents. An agent records each piece of work as one entry in
an append-only ledger (`append`) and reads entries back with filters (`list`).
Entries are never edited or removed, so the record of who did what, and when,
stays traceable and checkable. Agents and subagents that are given the same
ledger file add their entries to the one record.

The package is {DISTRIBUTION}; the command it installs is `{COMMAND}`.

Commands
--------
  ledger whoami             Identity from culture.yaml.
  ledger learn              This self-teaching prompt.
  ledger explain <path>...  Markdown docs for any noun/verb path.
  ledger overview           Descriptive snapshot of the agent.
  ledger doctor             Check the agent-identity invariants.
  ledger append <json>      Append one entry (agent, action, summary; refs, data).
  ledger list [filters]     Read entries: --agent --action --since --limit.
  ledger cli overview       Describe the CLI surface itself.

Machine-readable output
-----------------------
Every command supports --json. Errors in JSON mode emit
{{"code", "message", "remediation"}} to stderr. Stdout and stderr never mix.

Exit-code policy
----------------
  0 success
  1 user-input error (bad flag, bad path, missing arg)
  2 environment / setup error
  3+ reserved

Ledger
------
Append-only JSONL. The file is ${ENV_PATH} when that is set; otherwise
{DEFAULT_LOCATION_RULE}.
An entry holds agent, action and summary, optional refs and data, and a
generated id and UTC timestamp.
There is deliberately no edit, update, or delete verb.

More detail
-----------
  ledger explain ledger
"""


def _as_json_payload() -> dict[str, object]:
    return {
        "tool": DISTRIBUTION,
        "version": __version__,
        "purpose": (
            f"{summary()} Append-only entries are written with append and read back with list."
        ),
        "console_script": COMMAND,
        "commands": [
            {"path": ["whoami"], "summary": "Identity probe from culture.yaml."},
            {"path": ["learn"], "summary": "Self-teaching prompt."},
            {"path": ["explain"], "summary": "Markdown docs by path."},
            {"path": ["overview"], "summary": "Descriptive snapshot of the agent."},
            {"path": ["doctor"], "summary": "Check the agent-identity invariants."},
            {"path": ["append"], "summary": "Append one entry to the append-only ledger."},
            {"path": ["list"], "summary": "List ledger entries with filters."},
            {"path": ["cli", "overview"], "summary": "Describe the CLI surface."},
        ],
        "exit_codes": {
            "0": "success",
            "1": "user-input error",
            "2": "environment/setup error",
        },
        "json_support": True,
        "explain_pointer": f"{COMMAND} explain <path>",
    }


def cmd_learn(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        emit_result(_as_json_payload(), json_mode=True)
    else:
        emit_result(_TEXT, json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "learn",
        help="Print a structured self-teaching prompt for agent consumers.",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_learn)
