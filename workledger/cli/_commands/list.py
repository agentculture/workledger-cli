"""``workledger-cli list`` — read ledger entries, with simple filters."""

from __future__ import annotations

import argparse

from workledger.cli._commands._store import ledger_path, parse_timestamp, read_entries
from workledger.cli._errors import EXIT_USER_ERROR, CliError
from workledger.cli._output import emit_result


def cmd_list(args: argparse.Namespace) -> int:
    if args.limit is not None and args.limit < 1:
        raise CliError(
            code=EXIT_USER_ERROR,
            message="--limit must be >= 1",
            remediation="pass a positive integer",
        )
    since = parse_timestamp(args.since) if args.since else None
    entries = read_entries(ledger_path())
    if args.agent:
        entries = [e for e in entries if e.get("agent") == args.agent]
    if args.action:
        entries = [e for e in entries if e.get("action") == args.action]
    if since is not None:
        entries = [e for e in entries if parse_timestamp(e["timestamp"]) >= since]
    if args.limit is not None:
        entries = entries[-args.limit :]  # the most recent N, still in append order
    if getattr(args, "json", False):
        emit_result(entries, json_mode=True)
    else:
        text = "\n".join(
            f"{e['timestamp']}  {e['id']}  {e['agent']}  {e['action']}  {e['summary']}"
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
