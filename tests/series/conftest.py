"""The R4P evidence builders already stand up a real producer and receiver.

Stage 5-R4G's whole claim is that it aggregates *real* audit results, so it
reuses that harness rather than fabricating an `AuditOutcome`.
"""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent
for name in ("evidence", "transport", "turn", "audit", "protocol"):
    sys.path.insert(0, str(TESTS / name))
