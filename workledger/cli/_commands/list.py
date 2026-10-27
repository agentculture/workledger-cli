"""``workledger-cli list`` — read ledger entries, with simple filters."""

from __future__ import annotations

import argparse
from collections import deque

from workledger.cli._commands._store import (
    escape_control_chars,
    iter_entries,
    ledger_path,
    normalize_since,
)
from workledger.cli._errors import EXIT_USER_ERROR, CliError
from workledger.cli._output import emit_result


def cmd_list(args: argparse.Namespace) -> int:
    if args.limit is not None and args.limit < 1:
        raise CliError(
            code=EXIT_USER_ERROR,
            message="--limit must be >= 1",
            remediation="pass a positive integer",
        )
    since = normalize_since(args.since) if args.since else None
    stream = iter_entries(ledger_path())
    # Stored timestamps are validated fixed-format UTC, so string order == time order.
    matches = (
        e
        for e in stream
        if (not args.agent or e["agent"] == args.agent)
        and (not args.action or e["action"] == args.action)
        and (since is None or e["timestamp"] >= since)
    )
    # Most recent N only, still in append order; deque keeps memory bounded by N.
    entries = list(deque(matches, maxlen=args.limit) if args.limit is not None else matches)
    if getattr(args, "json", False):
        emit_result(entries, json_mode=True)
    else:
        text = "\n".join(
            f"{e['timestamp']}  {e['id']}  {escape_control_chars(e['agent'])}  "
            f"{escape_control_chars(e['action'])}  {escape_control_chars(e['summary'])}"
            for e in entries
        )
        emit_result(text if entries else "(no entries)", json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("list", help="List ledger entries (oldest first).")
    p.add_argument("--agent", help="Only entries by this agent.")
    p.add_argument("--action", help="Only entries with this action.")
    p.add_argument("--since", help="Only entries at/after this ISO-8601 timestamp (UTC if naive).")
    p.add_argument("--limit", type=int, help="Only the most recent N matching entries.")
    p.add_argument("--json", action="store_true", help="Emit a JSON array of entries.")
    p.set_defaults(func=cmd_list)
