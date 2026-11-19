"""The package's self-descriptions say what it is: a work ledger for agents.

The repo was scaffolded from a template for mesh agents, and its help text,
``learn``, ``explain`` and ``overview`` once described that template instead of
the ledger. These tests hold every user-facing self-description to the summary
in ``pyproject.toml`` and keep the template wording out.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from workledger.cli import main
from workledger.explain import known_paths

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

# Wording that describes the scaffold this repo started from, not the ledger.
_TEMPLATE_WORDING = ("template", "scaffold", "clone it", "rename the package")


def _summary() -> str:
    """The first sentence of the ``pyproject.toml`` description, lower-cased."""
    with _PYPROJECT.open("rb") as handle:
        description = tomllib.load(handle)["project"]["description"]
    return description.split(". ", 1)[0].rstrip(".").lower()


def _flat(text: str) -> str:
    """Lower-case and collapse whitespace, so argparse line wrapping is ignored."""
    return " ".join(text.lower().split())


def _assert_describes_the_ledger(text: str, where: str) -> None:
    flat = _flat(text)
    assert _summary() in flat, f"{where} does not carry the pyproject summary"
    for phrase in _TEMPLATE_WORDING:
        assert phrase not in flat, f"{where} still carries template wording: {phrase!r}"


def test_summary_is_the_ledger_summary() -> None:
    # Guards the helper: the tests below compare against this sentence.
    assert _summary() == "tracks work in a ledger so agents can prove what they did"


def test_help_description(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    _assert_describes_the_ledger(capsys.readouterr().out, "--help")


def test_learn_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0
    out = capsys.readouterr().out
    _assert_describes_the_ledger(out, "learn")
    assert "append-only" in out


def test_learn_text_keeps_the_rubric_topics(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0
    out = capsys.readouterr().out
    assert len(out) >= 200
    for topic in ("Purpose", "Commands", "Exit-code policy", "--json", "explain"):
        assert topic in out
    for verb in ("whoami", "learn", "explain", "overview", "doctor", "append", "list", "cli"):
        assert verb in out


def test_learn_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    _assert_describes_the_ledger(payload["purpose"], "learn --json purpose")
    _assert_describes_the_ledger(json.dumps(payload), "learn --json")


@pytest.mark.parametrize("path", [[], ["workledger-cli"], ["ledger"]])
def test_explain_root(path: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["explain", *path]) == 0
    out = capsys.readouterr().out
    _assert_describes_the_ledger(out, f"explain {' '.join(path)}".strip())
    assert "append-only" in out


def test_no_catalog_entry_carries_template_wording(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for path in known_paths():
        assert main(["explain", *path]) == 0
        flat = _flat(capsys.readouterr().out)
        for phrase in _TEMPLATE_WORDING:
            assert phrase not in flat, f"explain {' '.join(path)}: {phrase!r}"


def test_overview_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["overview"]) == 0
    _assert_describes_the_ledger(capsys.readouterr().out, "overview")


def test_overview_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["overview", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sections"][0]["title"] == "Purpose"
    _assert_describes_the_ledger(json.dumps(payload["sections"][0]), "overview --json purpose")


@pytest.mark.parametrize("verb", ["overview", "whoami", "learn", "explain", "doctor", "cli"])
def test_verb_help_has_no_template_wording(verb: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([verb, "--help"])
    assert exc.value.code == 0
    flat = _flat(capsys.readouterr().out)
    for phrase in _TEMPLATE_WORDING:
        assert phrase not in flat
