"""Tests for the append-only ledger verbs (append, list)."""

from __future__ import annotations

import io
import json
import os
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


def test_default_path_outside_repo_is_cwd_relative(tmp_path, monkeypatch, capsys) -> None:
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


def test_entry_cannot_be_modified_removed_or_id_supplied_through_cli(ledger, capsys) -> None:
    (first,) = seed(capsys, ENTRY)
    snapshot = ledger.read_bytes()
    for verb in ["edit", "update", "delete", "remove", "rm", "amend", "truncate", "clear"]:
        with pytest.raises(SystemExit) as exc:
            main([verb, first["id"], "--json"])
        assert exc.value.code == 1
        capsys.readouterr()
    # A caller cannot supply an id (so cannot forge/duplicate one); ledger untouched.
    assert main(["append", json.dumps({**ENTRY, "id": first["id"]}), "--json"]) == 1
    capsys.readouterr()
    assert ledger.read_bytes() == snapshot


def test_no_mutating_verb_registered() -> None:
    from workledger.cli import _build_parser

    sub = next(a for a in _build_parser()._actions if a.dest == "command")
    verbs = set(sub.choices)
    assert {"append", "list"} <= verbs
    assert not verbs & {"edit", "update", "delete", "remove", "rm", "amend", "truncate", "clear"}


# --- review-fix tests --------------------------------------------------------

GOOD_TS = "2026-01-01T00:00:00.000Z"


def good(**over) -> dict:
    return {"id": "i1", "timestamp": GOOD_TS, **ENTRY, "refs": [], "data": {}, **over}


def write_lines(ledger: Path, *lines: str) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("".join(line + "\n" for line in lines))


def err_of(capsys) -> dict:
    cap = capsys.readouterr()
    assert cap.out == "" and "Traceback" not in cap.err
    return json.loads(cap.err)


# 1. short writes / missing trailing newline


def test_short_write_is_completed(ledger, capsys, monkeypatch) -> None:
    real = os.write
    monkeypatch.setattr(os, "write", lambda fd, data: real(fd, bytes(data)[:5]))
    assert main(["append", json.dumps(ENTRY), "--json"]) == 0
    stored = json.loads(capsys.readouterr().out)
    assert json.loads(ledger.read_text())["id"] == stored["id"]
    assert ledger.read_bytes().endswith(b"\n")


def test_write_failure_midway_is_env_error(ledger, capsys, monkeypatch) -> None:
    real = os.write
    calls = []

    def flaky(fd, data):
        calls.append(1)
        if len(calls) > 1:
            raise OSError(28, "No space left on device")
        return real(fd, bytes(data)[:5])

    monkeypatch.setattr(os, "write", flaky)
    assert main(["append", json.dumps(ENTRY), "--json"]) == 2
    assert err_of(capsys)["code"] == 2


def test_append_refuses_when_file_lacks_trailing_newline(ledger, capsys) -> None:
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(b'{"half":')
    assert main(["append", json.dumps(ENTRY), "--json"]) == 2
    assert "newline" in err_of(capsys)["message"]
    assert ledger.read_bytes() == b'{"half":'


# 2. malformed-but-valid-JSON lines are corrupt (exit 2, line number)


@pytest.mark.parametrize(
    "bad",
    [
        "[1]",
        "{}",
        '{"timestamp":"bad"}',
        json.dumps(good(timestamp="2026-13-01T00:00:00.000Z")),
        json.dumps(good(timestamp="2026-01-01T00:00:00Z")),
        json.dumps(good(agent=3)),
        json.dumps(good(id="")),
        json.dumps(good(refs="x")),
        json.dumps(good(data=[])),
    ],
)
def test_list_malformed_line_is_corrupt(ledger, capsys, bad) -> None:
    write_lines(ledger, json.dumps(good(id="ok")), bad)
    for argv in (["list"], ["list", "--since", "2020-01-01", "--agent", "x"]):
        assert main([*argv, "--json"]) == 2
        err = err_of(capsys)
        assert err["code"] == 2 and "line 2" in err["message"]


# 3. encodings


def test_list_non_utf8_is_corrupt(ledger, capsys) -> None:
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(json.dumps(good()).encode() + b"\n" + b'{"a":"\xff"}\n')
    assert main(["list", "--json"]) == 2
    assert "line 2" in err_of(capsys)["message"]


def test_append_lone_surrogate_rejected_before_mkdir(ledger, capsys) -> None:
    assert main(["append", '{"agent":"a","action":"b","summary":"\\ud800"}', "--json"]) == 1
    assert err_of(capsys)["code"] == 1
    assert not ledger.parent.exists()


def test_append_raw_surrogate_in_argv_rejected(ledger, capsys) -> None:
    raw = '{"agent":"a","action":"b","summary":"\ud800"}'
    assert main(["append", raw, "--json"]) == 1
    assert err_of(capsys)["code"] == 1 and not ledger.parent.exists()


# 4. NaN / Infinity


@pytest.mark.parametrize("tok", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_append_rejects_non_finite(ledger, capsys, tok) -> None:
    raw = '{"agent":"a","action":"b","summary":"c","data":{"x":%s}}' % tok
    assert main(["append", raw, "--json"]) == 1
    assert err_of(capsys)["code"] == 1 and not ledger.parent.exists()


def test_stored_lines_are_strict_json(ledger, capsys) -> None:
    seed(capsys, {**ENTRY, "data": {"x": 1.5}})

    def boom(tok):
        raise ValueError(tok)

    json.loads(ledger.read_text(), parse_constant=boom)


# 5. control characters


@pytest.mark.parametrize("field", ["agent", "action", "summary"])
@pytest.mark.parametrize("ch", ["\n", "\r", "\x1b", "\u2028"])
def test_append_rejects_control_chars_in_required_fields(ledger, capsys, field, ch) -> None:
    assert main(["append", json.dumps({**ENTRY, field: f"a{ch}b"}), "--json"]) == 1
    assert err_of(capsys)["code"] == 1 and not ledger.parent.exists()


def test_list_text_escapes_control_chars(ledger, capsys) -> None:
    forged = "x\n2026-01-01T00:00:00.000Z  deadbeef  admin  approve  forged"
    write_lines(ledger, json.dumps(good(summary=forged)))
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert len(out.strip().splitlines()) == 1 and "\\x0a" in out


# 6. duplicate ids in the file


def test_list_duplicate_id_is_corrupt(ledger, capsys) -> None:
    write_lines(ledger, json.dumps(good()), json.dumps(good()))
    assert main(["list", "--json"]) == 2
    err = err_of(capsys)
    assert "duplicate" in err["message"] and "line 2" in err["message"]


# 7. default path


def test_default_path_resolves_to_git_toplevel(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("WORKLEDGER_PATH", raising=False)
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert main(["append", json.dumps(ENTRY)]) == 0
    assert (tmp_path / ".workledger" / "ledger.jsonl").exists()
    assert not (sub / ".workledger").exists()


def test_default_path_git_worktree_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("WORKLEDGER_PATH", raising=False)
    (tmp_path / ".git").write_text("gitdir: /elsewhere\n")
    (tmp_path / "s").mkdir()
    monkeypatch.chdir(tmp_path / "s")
    assert main(["append", json.dumps(ENTRY)]) == 0
    assert (tmp_path / ".workledger" / "ledger.jsonl").exists()


def test_env_overrides_git_toplevel(tmp_path, monkeypatch, ledger) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    assert main(["append", json.dumps(ENTRY)]) == 0
    assert ledger.exists() and not (tmp_path / ".workledger").exists()


def test_gitignore_covers_ledger_dir() -> None:
    root = Path(__file__).resolve().parent.parent
    assert ".workledger/" in (root / ".gitignore").read_text().splitlines()


# 8. streaming / limit / since normalisation


def test_list_limit_keeps_last_n_and_still_validates_all(ledger, capsys) -> None:
    write_lines(ledger, "{bad", *(json.dumps(good(id=f"i{n}")) for n in range(5)))
    assert main(["list", "--limit", "2", "--json"]) == 2
    capsys.readouterr()
    write_lines(ledger, *(json.dumps(good(id=f"i{n}")) for n in range(5)))
    assert main(["list", "--limit", "2", "--json"]) == 0
    assert [e["id"] for e in json.loads(capsys.readouterr().out)] == ["i3", "i4"]


def test_list_since_no_per_line_datetime_parsing(ledger, capsys, monkeypatch) -> None:
    from workledger.cli._commands import _store

    write_lines(ledger, *(json.dumps(good(id=f"i{n}")) for n in range(3)))
    calls = []
    real = _store.parse_timestamp
    monkeypatch.setattr(_store, "parse_timestamp", lambda v: calls.append(v) or real(v))
    assert main(["list", "--since", "2025-12-31T23:00:00-00:30", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 3
    assert calls == ["2025-12-31T23:00:00-00:30"]


@pytest.mark.parametrize(
    ("since", "n"),
    [
        ("2026-01-01T00:00:00.000Z", 1),
        ("2026-01-01T00:00:00.0005Z", 0),  # rounds up: entry at .000 is earlier
        ("2026-01-01T01:00:00+01:00", 1),  # offset normalised to UTC
        ("2026-01-01T00:00:00.000-01:00", 0),
    ],
)
def test_list_since_normalised(ledger, capsys, since, n) -> None:
    write_lines(ledger, json.dumps(good()))
    assert main(["list", "--since", since, "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == n


# 9. interactive stdin


def test_append_stdin_tty_fails_fast(ledger, capsys, monkeypatch) -> None:
    class Tty(io.StringIO):
        def isatty(self) -> bool:
            return True

        def read(self, *a):
            raise AssertionError("must not block on a terminal")

    monkeypatch.setattr("sys.stdin", Tty())
    assert main(["append", "--stdin", "--json"]) == 1
    assert err_of(capsys)["code"] == 1 and not ledger.parent.exists()
