"""Entry point for ``python -m workledger``."""

from __future__ import annotations

import sys

from workledger.cli import main

if __name__ == "__main__":
    sys.exit(main())
