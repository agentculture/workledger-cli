"""What this package calls itself: one source for every self-description.

The distribution is ``workledger-cli``; the command it installs is ``ledger``.
The one-sentence summary comes from the installed distribution's metadata (the
``description`` in ``pyproject.toml``), so the help text, ``learn``, ``explain``
and ``overview`` cannot drift from it.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, metadata

DISTRIBUTION = "workledger-cli"
COMMAND = "ledger"

# Used only when the distribution's metadata cannot be read.
_FALLBACK_SUMMARY = "Tracks work in a ledger so agents can prove what they did."


def summary() -> str:
    """The first sentence of the distribution's Summary, ending in a full stop."""
    try:
        text = metadata(DISTRIBUTION)["Summary"]
    except PackageNotFoundError:
        return _FALLBACK_SUMMARY
    first = (text or "").split(". ", 1)[0].strip().rstrip(".")
    return f"{first}." if first else _FALLBACK_SUMMARY
