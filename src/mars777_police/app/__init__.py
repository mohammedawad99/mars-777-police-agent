"""Local application layer.

Stage 3C implements only the **local effect step** of a turn: it validates a
single proposed action through the already-built domain rules and advances this
agent's own truth. Everything a peer exchange would add is deliberately absent -
no protocol messages, no commit/acknowledge/reveal, no public network, no
asynchronous orchestration and no cryptography.

Two boundaries are deliberate and load-bearing:

* **No terminal outcome is declared here.** Capture takes precedence over
  survival and is established by deterministic evaluation on *both* peers, never
  by one side's assertion (PRD01-FR-053/FR-055). A peer holding only its own
  truth cannot conclude "not captured", so it must not conclude "survival"
  either. Terminal evaluation happens once the verified public facts exist.
* **No pheromone lifecycle runs here.** Ch 4 p.43 evolves the field at the end
  of each *full* turn - after both agents have completed their move - which a
  purely local action step cannot know. That physics stays a domain primitive
  until the resolved turn cycle owns its timing.

The layer depends inward on ``domain`` only; ``domain`` never imports it.
"""

from .turn_service import (
    ActionKind,
    ActionsExhaustedError,
    ApplicationError,
    BarrierAction,
    InvalidActionError,
    LocalActionResult,
    LocalTurnService,
    MoveAction,
    UnsupportedActionError,
)

__all__ = [
    "ActionKind",
    "ActionsExhaustedError",
    "ApplicationError",
    "BarrierAction",
    "InvalidActionError",
    "LocalActionResult",
    "LocalTurnService",
    "MoveAction",
    "UnsupportedActionError",
]
