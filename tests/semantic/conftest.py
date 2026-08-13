"""Reuse the audit, evidence and config builders the earlier stages proved."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in ("audit", "evidence", "turn", "app", "series"):
    sys.path.insert(0, str(TESTS / name))
