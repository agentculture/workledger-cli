"""The package's self-descriptions say what it is: a work ledger for agents.

The repo was scaffolded from a mesh-agent starter, and its help text, ``learn``,
``explain`` and ``overview`` once described that starter instead of the ledger.
These tests hold every user-facing self-description to the summary in
``pyproject.toml``, to the command that is actually installed (``ledger``), and
to what the store really does when it picks the ledger file.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import tomllib
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

from workledger import _about
from workledger.cli import _build_parser, main
from workledger.explain import known_paths

_REPO = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO / "pyproject.toml"
_JSON_FLAG = "--json"
_OVERVIEW = "overview"
_SECTIONS = "sections"

# Phrases left over from the starter this repo was scaffolded from. Whole
# phrases, not single words, so honest later wording is not refused.
_LEFTOVER_PHRASES = (
    "clonable template",
    "this template",
    "clone it",
    "rename the package",
    "make it your own",
    "register your own",
    "sibling-pattern",
)

# How the store picks the default ledger file (see ``_store.ledger_path``).
_PATH_RULE = "nearest ancestor directory that contains .git (else the current directory)"
_WRONG_PATH_RULE = "git toplevel"


def _verbs() -> list[str]:
    """Every top-level verb the parser registers."""
    actions = _build_parser()._actions
    sub = next(a for a in actions if isinstance(a, argparse._SubParsersAction))
    return list(sub.choices)


_VERBS = _verbs()
# The package name followed by a verb: an invocation that is not installed.
_NOT_INSTALLED = re.compile(r"workledger-cli\s+(?:" + "|".join(map(re.escape, _VERBS)) + r")\b")


def _pyproject_summary() -> str:
    """The first sentence of the ``pyproject.toml`` description."""
    with _PYPROJECT.open("rb") as handle:
        description = tomllib.load(handle)["project"]["description"]
    return description.split(". ", 1)[0].rstrip(".") + "."


def _flat(text: str) -> str:
    """Lower-case, drop backticks and collapse whitespace (line wrapping is ignored)."""
    return " ".join(text.lower().replace("`", "").split())


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    """Run the CLI and return stdout and stderr together, whatever the exit."""
    with contextlib.suppress(SystemExit):
        main(argv)
    captured = capsys.readouterr()
    return captured.out + captured.err


def _assert_no_leftovers(text: str, where: str) -> None:
    flat = _flat(text)
    for phrase in _LEFTOVER_PHRASES:
        assert phrase not in flat, f"{where} still carries starter wording: {phrase!r}"


def _assert_describes_the_ledger(text: str, where: str) -> None:
    assert _flat(_about.summary()) in _flat(text), f"{where} does not carry the summary"
    _assert_no_leftovers(text, where)


# --- one source for the summary -------------------------------------------


def test_summary_matches_pyproject() -> None:
    assert _about.summary() == _pyproject_summary()
    assert _about.summary() == "Tracks work in a ledger so agents can prove what they did."


def test_summary_fallback_matches_pyproject(monkeypatch: pytest.MonkeyPatch) -> None:
    def _missing(name: str) -> None:
        raise PackageNotFoundError(name)

    monkeypatch.setattr(_about, "metadata", _missing)
    assert _about.summary() == _pyproject_summary()


def test_command_is_the_installed_script() -> None:
    with _PYPROJECT.open("rb") as handle:
        scripts = tomllib.load(handle)["project"]["scripts"]
    assert list(scripts) == [_about.COMMAND]


# --- every surface carries the summary ------------------------------------


@pytest.mark.parametrize(
    "argv",
    [[], ["learn"], ["explain"], ["explain", "workledger-cli"], ["explain", "ledger"], [_OVERVIEW]],
)
def test_surface_describes_the_ledger(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(argv) == 0
    _assert_describes_the_ledger(capsys.readouterr().out, " ".join(argv) or "--help")


@pytest.mark.parametrize("argv", [["learn"], ["explain"]])
def test_surface_says_append_only(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(argv) == 0
    assert "append-only" in capsys.readouterr().out


def test_learn_json_describes_the_ledger(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn", _JSON_FLAG]) == 0
    payload = json.loads(capsys.readouterr().out)
    _assert_describes_the_ledger(payload["purpose"], "learn --json purpose")
    assert payload["console_script"] == _about.COMMAND
    assert payload["explain_pointer"] == "ledger explain <path>"


# --- learn keeps what the rubric asks for ---------------------------------


def test_learn_text_keeps_the_rubric_topics(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0
    out = capsys.readouterr().out
    assert len(out) >= 200
    for topic in ("Purpose", "Commands", "Exit-code policy", _JSON_FLAG, "explain"):
        assert topic in out


@pytest.mark.parametrize("verb", _VERBS)
def test_learn_text_has_a_row_for_each_verb(verb: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0
    row = re.compile(rf"^  ledger {re.escape(verb)}\b.*\S", re.MULTILINE)
    assert row.search(capsys.readouterr().out), f"no command row for {verb!r}"


def test_learn_json_lists_each_verb(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn", _JSON_FLAG]) == 0
    payload = json.loads(capsys.readouterr().out)
    listed = {command["path"][0] for command in payload["commands"]}
    assert listed == set(_VERBS)


def test_every_verb_has_a_catalog_entry() -> None:
    assert {(verb,) for verb in _VERBS} <= set(known_paths())


# --- the invocation is the installed command ------------------------------


def _user_facing_argvs() -> list[list[str]]:
    argvs: list[list[str]] = [[], ["--help"], ["learn"], ["learn", _JSON_FLAG]]
    argvs.extend([verb, "--help"] for verb in _VERBS)
    argvs.extend(["explain", *path] for path in known_paths())
    argvs.extend(
        [
            [_OVERVIEW],
            [_OVERVIEW, _JSON_FLAG],
            ["cli", _OVERVIEW],
            ["cli", _OVERVIEW, _JSON_FLAG],
            ["doctor"],
            ["bogus"],
            ["explain", "nonexistent"],
            ["explain", "nonexistent", _JSON_FLAG],
            ["append", "--bogus"],
            ["append"],
        ]
    )
    return argvs


@pytest.mark.parametrize("argv", _user_facing_argvs(), ids=" ".join)
def test_no_output_names_an_uninstalled_command(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    output = _run(argv, capsys)
    assert output.strip()
    assert not _NOT_INSTALLED.search(output), _NOT_INSTALLED.search(output)


def test_help_usage_names_the_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: ledger" in capsys.readouterr().out


def test_parse_error_hint_names_the_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert "hint: run 'ledger --help'" in _run(["bogus"], capsys)


def test_explain_error_hint_names_the_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert "ledger explain ledger" in _run(["explain", "nonexistent"], capsys)


def test_readme_names_the_installed_command() -> None:
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    assert not _NOT_INSTALLED.search(readme)
    _assert_no_leftovers(readme, "README.md")


# --- no starter wording anywhere ------------------------------------------


@pytest.mark.parametrize("verb", _VERBS)
def test_verb_help_has_no_starter_wording(verb: str, capsys: pytest.CaptureFixture[str]) -> None:
    _assert_no_leftovers(_run([verb, "--help"], capsys), f"{verb} --help")


@pytest.mark.parametrize("path", known_paths(), ids=" ".join)
def test_catalog_entry_has_no_starter_wording(
    path: tuple[str, ...], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["explain", *path]) == 0
    _assert_no_leftovers(capsys.readouterr().out, f"explain {' '.join(path)}")


def test_parser_source_has_no_starter_comment() -> None:
    source = (_REPO / "workledger" / "cli" / "__init__.py").read_text(encoding="utf-8")
    assert "my_noun" not in source
    _assert_no_leftovers(source, "workledger/cli/__init__.py")


# --- the default ledger path is described as the store resolves it --------


@pytest.mark.parametrize(
    "argv",
    [["learn"], ["explain"], ["explain", "append"], [_OVERVIEW], [_OVERVIEW, _JSON_FLAG]],
)
def test_default_path_rule_is_stated(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(argv) == 0
    flat = _flat(capsys.readouterr().out)
    assert _PATH_RULE in flat
    assert "$workledger_path" in flat
    assert _WRONG_PATH_RULE not in flat


def test_readme_states_the_default_path_rule() -> None:
    flat = _flat((_REPO / "README.md").read_text(encoding="utf-8"))
    assert _PATH_RULE in flat
    assert _WRONG_PATH_RULE not in flat


# --- overview --------------------------------------------------------------


def _overview_sections(capsys: pytest.CaptureFixture[str]) -> list[dict[str, object]]:
    assert main([_OVERVIEW, _JSON_FLAG]) == 0
    return json.loads(capsys.readouterr().out)[_SECTIONS]


def test_overview_json_keeps_identity_first(capsys: pytest.CaptureFixture[str]) -> None:
    titles = [section["title"] for section in _overview_sections(capsys)]
    assert titles == ["Identity", "Verbs", "Repository artifacts", "Purpose"]


def test_overview_json_purpose_describes_the_ledger(capsys: pytest.CaptureFixture[str]) -> None:
    purpose = _overview_sections(capsys)[-1]
    _assert_describes_the_ledger(json.dumps(purpose), "overview --json purpose")


def test_overview_artifacts_exist(capsys: pytest.CaptureFixture[str]) -> None:
    artifacts = _overview_sections(capsys)[2]
    assert artifacts["items"]
    for item in artifacts["items"]:
        names = str(item).split(" — ", 1)[0]
        for name in names.split(" + "):
            assert (_REPO / name).exists(), f"overview names {name!r}, which is not in the repo"


def test_readme_skill_count_matches_the_tree() -> None:
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    skills = [p for p in (_REPO / ".claude" / "skills").iterdir() if (p / "SKILL.md").is_file()]
    assert f"{len(skills)} skills" in readme
