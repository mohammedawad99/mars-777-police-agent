"""Reuse the builders the earlier stages already proved, rather than rebuild them."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "boot",
    "composition_root",
    "evidence",
    "network",
    "public_launch",
    "runner",
    "series",
    "session",
    "transport",
    "turn",
    "audit",
    "protocol",
    "interop",
    "series_lifecycle",
    "semantic",
    "app",
):
    sys.path.insert(0, str(TESTS / name))
