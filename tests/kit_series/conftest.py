"""Reuse the pinned vector material and the fixtures earlier stages already proved."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "interop",
    "transport",
    "kit_transport",
    "runner",
    "evidence",
    "series",
    "session",
    "turn",
    "audit",
    "protocol",
    "app",
    "composition_root",
    "network",
):
    sys.path.insert(0, str(TESTS / name))
