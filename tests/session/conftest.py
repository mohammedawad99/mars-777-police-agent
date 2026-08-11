"""Shared import roots: this stage wires runtimes the other suites already build.

The point of Stage 5-R3R is that the production adapter reaches **real** owners,
so the fixtures reuse the turn, audit and transport builders rather than growing
a fourth copy of a declaration, a board or a sealed record.
"""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in ("transport", "turn", "audit", "protocol"):
    sys.path.insert(0, str(TESTS / name))
