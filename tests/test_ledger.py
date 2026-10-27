"""Tests for the append-only ledger verbs (append, list)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from workledger.cli import main

ENTRY = {"agent": "assoc", "action": "read", "summary": "read file"}


@pytest.fixture
def ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "sub" / "ledger.jsonl"
    monkeypatch.setenv("WORKLEDGER_PATH", str(path))
    return path


def run_append(capsys, entry: dict, *extra: str):
    rc = main(["append", json.dumps(entry), *extra])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_append_json_returns_stored_entry(ledger, capsys) -> None:
    rc, out, err = run_append(capsys, {**ENTRY, "refs": ["abc"], "data": {"n": 1}}, "--json")
    assert rc == 0 and err == ""
    stored = json.loads(out)
    assert stored["agent"] == "assoc" and stored["refs"] == ["abc"] and stored["data"] == {"n": 1}
    assert len(stored["id"]) == 32 and stored["timestamp"].endswith("Z")
    assert json.loads(ledger.read_text().splitlines()[0]) == stored


def test_append_defaults_and_text_mode(ledger, capsys) -> None:
    rc, out, _ = run_append(capsys, ENTRY)
    assert rc == 0 and out.startswith("appended ")
    stored = json.loads(ledger.read_text())
    assert stored["refs"] == [] and stored["data"] == {}


def test_append_stdin(ledger, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(ENTRY)))
    assert main(["append", "--stdin", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["summary"] == "read file"


@pytest.mark.parametrize(
    "argv",
    [
        ["append"],
        ["append", "not json"],
        ["append", "[1]"],
        ["append", '{"agent":"a","action":"b"}'],
        ["append", '{"agent":"a","action":"b","summary":""}'],
        ["append", '{"agent":"a","action":"b","summary":"c","extra":1}'],
        ["append", '{"agent":"a","action":"b","summary":"c","id":"x"}'],
        ["append", '{"agent":"a","action":"b","summary":"c","timestamp":"x"}'],
        ["append", '{"agent":"a","action":"b","summary":"c","refs":"x"}'],
        ["append", '{"agent":"a","action":"b","summary":"c","refs":[1]}'],
        ["append", '{"agent":"a","action":"b","summary":"c","data":[]}'],
        ["append", "{}", "--stdin"],
    ],
)
def test_append_user_errors(ledger, capsys, argv) -> None:
    assert main(argv + ["--json"]) == 1
    cap = capsys.readouterr()
    assert cap.out == ""
    err = json.loads(cap.err)
    assert err["code"] == 1 and err["message"] and err["remediation"]
    assert not ledger.exists()


def test_list_empty_and_missing(ledger, capsys) -> None:
    assert main(["list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []
    assert main(["list"]) == 0
    assert "(no entries)" in capsys.readouterr().out


def seed(capsys, *entries: dict) -> list[dict]:
    out = []
    for e in entries:
        _, o, _ = run_append(capsys, e, "--json")
        out.append(json.loads(o))
    return out


def test_list_filters(ledger, capsys) -> None:
    a, b, c = seed(
        capsys,
        {**ENTRY, "agent": "x"},
        {**ENTRY, "agent": "y", "action": "write"},
        {**ENTRY, "agent": "x", "action": "write"},
    )
    main(["list", "--json"])
    assert [e["id"] for e in json.loads(capsys.readouterr().out)] == [a["id"], b["id"], c["id"]]
    main(["list", "--agent", "x", "--json"])
    assert [e["id"] for e in json.loads(capsys.readouterr().out)] == [a["id"], c["id"]]
    main(["list", "--agent", "x", "--action", "write", "--json"])
    assert [e["id"] for e in json.loads(capsys.readouterr().out)] == [c["id"]]
    main(["list", "--limit", "2", "--json"])
    assert [e["id"] for e in json.loads(capsys.readouterr().out)] == [b["id"], c["id"]]
    main(["list"])
    assert a["id"] in capsys.readouterr().out


def test_list_since(ledger, capsys) -> None:
    old = {"id": "o", "timestamp": "2020-01-01T00:00:00.000Z", **ENTRY, "refs": [], "data": {}}
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(old) + "\n")
    (new,) = seed(capsys, ENTRY)
    main(["list", "--since", "2021-01-01T00:00:00Z", "--json"])
    assert [e["id"] for e in json.loads(capsys.readouterr().out)] == [new["id"]]
    main(["list", "--since", "2020-01-01", "--json"])  # naive = UTC
    assert len(json.loads(capsys.readouterr().out)) == 2


@pytest.mark.parametrize("argv", [["--since", "yesterday"], ["--limit", "0"], ["--limit", "x"]])
def test_list_bad_args(ledger, capsys, argv) -> None:
    try:
        rc = main(["list", "--json", *argv])
    except SystemExit as exc:  # argparse-level error routed via the structured contract
        rc = exc.code
    assert rc == 1
    cap = capsys.readouterr()
    assert cap.out == "" and json.loads(cap.err)["code"] == 1


def test_list_corrupt_ledger_is_env_error(ledger, capsys) -> None:
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{not json\n")
    assert main(["list", "--json"]) == 2
    assert json.loads(capsys.readouterr().err)["code"] == 2


def test_default_path_is_relative_workledger_dir(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("WORKLEDGER_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["append", json.dumps(ENTRY)]) == 0
    assert (tmp_path / ".workledger" / "ledger.jsonl").exists()


# --- append-only guarantee -------------------------------------------------


def test_append_never_rewrites_earlier_bytes(ledger, capsys) -> None:
    (first,) = seed(capsys, ENTRY)
    before = ledger.read_bytes()
    (second,) = seed(capsys, {**ENTRY, "summary": "again"})
    after = ledger.read_bytes()
    assert after.startswith(before) and len(after) > len(before)
    ids = [json.loads(line)["id"] for line in after.splitlines()]
    assert ids == [first["id"], second["id"]] and len(set(ids)) == 2


def test_entry_cannot_be_modified_or_removed_through_cli(ledger, capsys) -> None:
    (first,) = seed(capsys, ENTRY)
    snapshot = ledger.read_bytes()
    for verb in ["edit", "update", "delete", "remove", "rm", "amend", "truncate", "clear"]:
        with pytest.raises(SystemExit) as exc:
            main([verb, first["id"], "--json"])
        assert exc.value.code == 1
        capsys.readouterr()
    # Re-appending with the same id is refused, and the ledger is untouched.
    assert main(["append", json.dumps({**ENTRY, "id": first["id"]}), "--json"]) == 1
    capsys.readouterr()
    assert ledger.read_bytes() == snapshot


def test_no_mutating_verb_registered() -> None:
    from workledger.cli import _build_parser

    sub = next(a for a in _build_parser()._actions if a.dest == "command")
    verbs = set(sub.choices)
    assert {"append", "list"} <= verbs
    assert not verbs & {"edit", "update", "delete", "remove", "rm", "amend", "truncate", "clear"}
