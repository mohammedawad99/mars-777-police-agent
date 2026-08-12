"""Reuse the builders and live-server helper the earlier stages already proved."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in ("runner", "evidence", "series", "session", "transport", "turn", "audit", "protocol"):
    sys.path.insert(0, str(TESTS / name))
