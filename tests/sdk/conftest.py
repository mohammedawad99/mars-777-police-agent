"""Reuse the builders the earlier stages already proved, rather than rebuild them."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in (
    "boot",
    "composition_root",
    "runner",
    "evidence",
    "series",
    "series_lifecycle",
    "session",
    "transport",
    "turn",
    "audit",
    "protocol",
    "interop",
):
    sys.path.insert(0, str(TESTS / name))
