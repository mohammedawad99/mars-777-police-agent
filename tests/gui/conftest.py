"""Reuse the builders that already produce real observations and real artifacts."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "boot",
    "composition_root",
    "evidence",
    "runner",
    "series",
    "series_lifecycle",
    "semantic",
    "session",
    "transport",
    "turn",
    "audit",
    "protocol",
    "interop",
    "app",
    "replay",
):
    sys.path.insert(0, str(TESTS / name))
