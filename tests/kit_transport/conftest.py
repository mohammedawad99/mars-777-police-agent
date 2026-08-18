"""Reuse the pinned vector material and the fixtures earlier stages already proved."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "interop",
    "transport",
    "runner",
    "evidence",
    "series",
    "session",
    "turn",
    "audit",
    "protocol",
    "composition_root",
):
    sys.path.insert(0, str(TESTS / name))
