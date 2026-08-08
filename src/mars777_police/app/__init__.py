"""Local application layer.

Implemented so far: the local **effect step** of a turn (Stage 3C), the frozen
protocol **phase machine** (Stage 4A), its **transition evidence** (Stage 4B),
the local **series orchestrator** (Stage 4C), the shared **protocol value
representations** (Stage 4F) and the first **peer-message contracts** - the turn
cursor and the commitment (Stage 4E). Everything else a peer exchange would add
is deliberately absent: nine of the ten peer-visible families stay blocked on
contracts nothing freezes yet, so there is no acknowledgement, no reveal, no wire
mapping, no public network, no asynchronous orchestration and no cryptography.

Three boundaries are deliberate and load-bearing:

* **No terminal outcome is declared here.** Capture takes precedence over
  survival and is established by deterministic evaluation on *both* peers, never
  by one side's assertion (PRD01-FR-053/FR-055). A peer holding only its own
  truth cannot conclude "not captured", so it must not conclude "survival"
  either. Terminal evaluation happens once the verified public facts exist.
* **No pheromone lifecycle runs here.** Ch 4 p.43 evolves the field at the end
  of each *full* turn - after both agents have completed their move - which a
  purely local action step cannot know. That physics stays a domain primitive
  until the resolved turn cycle owns its timing.
* **Transition evidence is structural, not authenticated.** It records a legal
  phase pair and supports phase-path replay only; hashes, signatures, nonces and
  official artifacts belong to PRD-06 / replay.

The orchestrator owns the current sub-game cursor and composes the phase
machine; recording the per-sub-game and cumulative score (`STATE_OWNERSHIP.md`)
remains a **pending** later responsibility, because it needs truthful terminal
facts that do not exist yet.

The layer depends inward on ``domain`` only; ``domain`` never imports it.
"""

from .orchestrator import (
    IllegalSubGameBranchError,
    LocalOrchestrator,
    OrchestratorResult,
)
from .peer_messages import Commitment, TurnCursor
from .protocol_values import FinalAuditVerdict, InvalidDigestError, Sha256Digest
from .state_machine import (
    FAULT_PHASES,
    NORMAL_PHASES,
    IllegalTransitionError,
    ProtocolMachine,
    ProtocolPhase,
    TransitionEvidence,
    TransitionResult,
)
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
    "FAULT_PHASES",
    "NORMAL_PHASES",
    "ActionKind",
    "ActionsExhaustedError",
    "ApplicationError",
    "BarrierAction",
    "Commitment",
    "FinalAuditVerdict",
    "IllegalSubGameBranchError",
    "IllegalTransitionError",
    "InvalidActionError",
    "InvalidDigestError",
    "LocalActionResult",
    "LocalOrchestrator",
    "LocalTurnService",
    "MoveAction",
    "OrchestratorResult",
    "ProtocolMachine",
    "ProtocolPhase",
    "Sha256Digest",
    "TransitionEvidence",
    "TransitionResult",
    "TurnCursor",
    "UnsupportedActionError",
]
