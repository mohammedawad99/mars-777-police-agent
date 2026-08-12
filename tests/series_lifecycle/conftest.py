"""Reuse the composition builders R5 already proved."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "boot",
    "composition_root",
    "runner",
    "evidence",
    "series",
    "session",
    "transport",
    "turn",
    "audit",
    "protocol",
):
    sys.path.insert(0, str(TESTS / name))
