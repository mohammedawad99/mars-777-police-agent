"""Make the research package importable, and reuse the production builders."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"
sys.path.insert(0, str(ROOT))
for name in ("app", "domain", "runner", "protocol", "audit", "semantic"):
    sys.path.insert(0, str(TESTS / name))
