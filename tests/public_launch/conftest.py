"""Reuse the network and transport fixtures the earlier stages already proved."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "network",
    "transport",
    "kit_series",
    "interop",
    "composition_root",
    "runner",
    "evidence",
    "series",
    "session",
    "turn",
    "audit",
    "protocol",
    "app",
    "boot",
    "series_lifecycle",
):
    sys.path.insert(0, str(TESTS / name))
