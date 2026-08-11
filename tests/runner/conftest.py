"""Reuse the builders the earlier stages already proved, rather than a fourth copy."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in ("evidence", "series", "session", "transport", "turn", "audit", "protocol"):
    sys.path.insert(0, str(TESTS / name))
