"""Reuse the builders that already produce real agreed results on disk."""

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
    "gatekeeper",
    "replay",
):
    sys.path.insert(0, str(TESTS / name))
