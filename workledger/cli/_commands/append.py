"""``workledger-cli append`` — append one entry to the ledger (the only write verb)."""

from __future__ import annotations

import argparse
import sys

from workledger.cli._commands._store import (
    append_entry,
    ledger_path,
    loads_strict,
    validate_input,
)
from workledger.cli._errors import EXIT_USER_ERROR, CliError
from workledger.cli._output import emit_result


def cmd_append(args: argparse.Namespace) -> int:
    if args.entry is not None and args.stdin:
        raise CliError(
            code=EXIT_USER_ERROR,
            message="pass the entry as an argument or with --stdin, not both",
            remediation="drop one of them",
        )
    if args.entry is None and not args.stdin:
        raise CliError(
            code=EXIT_USER_ERROR,
            message="no entry given",
            remediation="pass a JSON object argument, or use --stdin",
        )
    if args.stdin and sys.stdin.isatty():
        raise CliError(
            code=EXIT_USER_ERROR,
            message="--stdin was given but stdin is an interactive terminal",
            remediation="pipe the entry in (echo '{...}' | workledger-cli append --stdin)",
        )
    text = sys.stdin.read() if args.stdin else args.entry
    try:
        raw = loads_strict(text)
    except (ValueError, RecursionError) as err:  # JSONDecodeError is a ValueError
        raise CliError(
            code=EXIT_USER_ERROR,
            message=f"entry is not valid JSON: {err}",
            remediation='e.g. \'{"agent":"a","action":"edit","summary":"did x"}\'',
        ) from err
    entry = append_entry(ledger_path(), validate_input(raw))
    if getattr(args, "json", False):
        emit_result(entry, json_mode=True)
    else:
        emit_result(f"appended {entry['id']} ({entry['timestamp']})", json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "append",
        help="Append one JSON entry to the append-only ledger.",
    )
    p.add_argument(
        "entry",
        nargs="?",
        help="Entry as a JSON object: agent, action, summary (required); refs, data (optional).",
    )
    p.add_argument("--stdin", action="store_true", help="Read the entry JSON from stdin.")
    p.add_argument("--json", action="store_true", help="Emit the stored entry as JSON.")
    p.set_defaults(func=cmd_append)
