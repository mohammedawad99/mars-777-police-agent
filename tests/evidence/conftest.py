"""The turn suite already builds a real `TurnProtocolRuntime`; reuse it.

Stage 5-R4P must prove its produced `Commitment` is accepted by the real live
runtime, and growing a second copy of a board and a turn service to do that
would be exactly the duplication these stages keep refusing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "turn"))
