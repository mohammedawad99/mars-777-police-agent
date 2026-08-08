"""The frozen protocol phase machine.

`app.state_machine` is the sole authority on what may happen next
(`MODULE_BOUNDARIES.md`), and it owns exactly one fact: the current phase
(`STATE_OWNERSHIP.md` - "State-machine current state | app.state_machine").
Everything else stays where it already lives: the step count in `domain.truth`,
the sub-game index in `app.orchestrator`, the barrier facts on the board.

Stage 4A enforces phase ORDER only. COMMIT_SENT, ACKNOWLEDGED, REVEAL and
FINAL_AUDIT are lifecycle labels; none of the cryptography, message bodies,
serialization or transport they will later carry exists yet, and this module
performs no I/O and holds no game state. Conditional branches are decided by
the caller, which supplies the target phase; this module validates only whether
that step is legal, never the facts behind the choice.

The graph in ``_ALLOWED`` is transcribed from the "Allowed next" column of
`STATE_MACHINE.md` §2 and is the single authoritative representation - the
transition check reads it rather than re-encoding the graph in branching logic.

One edge is an implementation-discovered architecture correction (Stage
4A-FIX1): ``TECHNICAL_LOSS -> SUBGAME_COMPLETE``. The same table already makes
"technical loss" an entry condition of SUBGAME_COMPLETE and tells TECHNICAL_LOSS
to "proceed per series rules", and R5 names only TAMPERED and FAILED as never
returning to play. TAMPERED and FAILED stay absorbing, untouched.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class IllegalTransitionError(Exception):
    """Raised when a requested phase step is not in the frozen graph.

    Outer layers map this onto the locked codes: an out-of-order inbound event
    is ``E-PROTO-STALE``, an internal misuse is ``E-LOCAL-DEFECT``
    (`ERROR_MODEL.md`). The message carries only the two phase names.
    """


class ProtocolPhase(StrEnum):
    """The 18 phases of `STATE_MACHINE.md` §1/§2."""

    BOOT = "BOOT"
    STEP0_NEGOTIATION = "STEP0_NEGOTIATION"
    CONFIG_NEGOTIATION = "CONFIG_NEGOTIATION"
    CONFIG_LOCKED = "CONFIG_LOCKED"
    READY = "READY"
    TURN_DECISION = "TURN_DECISION"
    COMMIT_SENT = "COMMIT_SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REVEAL = "REVEAL"
    VALIDATING = "VALIDATING"
    TURN_COMPLETE = "TURN_COMPLETE"
    SUBGAME_COMPLETE = "SUBGAME_COMPLETE"
    SERIES_COMPLETE = "SERIES_COMPLETE"
    FINAL_AUDIT = "FINAL_AUDIT"
    REPORT_READY = "REPORT_READY"
    FAILED = "FAILED"
    TAMPERED = "TAMPERED"
    TECHNICAL_LOSS = "TECHNICAL_LOSS"


_P: Final = ProtocolPhase

"""The 15 normal lifecycle phases, in `STATE_MACHINE.md` §2 table order."""

_ALLOWED: Final[dict[ProtocolPhase, tuple[ProtocolPhase, ...]]] = {
    _P.BOOT: (_P.STEP0_NEGOTIATION, _P.FAILED),
    _P.STEP0_NEGOTIATION: (_P.CONFIG_NEGOTIATION, _P.FAILED),
    _P.CONFIG_NEGOTIATION: (_P.CONFIG_LOCKED, _P.FAILED),
    _P.CONFIG_LOCKED: (_P.READY, _P.FAILED),
    _P.READY: (_P.TURN_DECISION, _P.SUBGAME_COMPLETE),
    _P.TURN_DECISION: (_P.COMMIT_SENT, _P.FAILED),
    _P.COMMIT_SENT: (_P.ACKNOWLEDGED, _P.FAILED, _P.TECHNICAL_LOSS),
    _P.ACKNOWLEDGED: (_P.REVEAL, _P.FAILED),
    _P.REVEAL: (_P.VALIDATING, _P.FAILED, _P.TECHNICAL_LOSS),
    _P.VALIDATING: (_P.TURN_COMPLETE, _P.TAMPERED, _P.TECHNICAL_LOSS),
    _P.TURN_COMPLETE: (_P.TURN_DECISION, _P.SUBGAME_COMPLETE),
    _P.SUBGAME_COMPLETE: (_P.READY, _P.SERIES_COMPLETE),
    _P.SERIES_COMPLETE: (_P.FINAL_AUDIT,),
    _P.FINAL_AUDIT: (_P.REPORT_READY, _P.TAMPERED),
    _P.REPORT_READY: (),
    _P.FAILED: (),
    _P.TAMPERED: (),
    _P.TECHNICAL_LOSS: (_P.SUBGAME_COMPLETE,),
}


FAULT_PHASES: Final[tuple[ProtocolPhase, ...]] = (_P.FAILED, _P.TAMPERED, _P.TECHNICAL_LOSS)
"""The 3 phases listed as "terminal / fault" in `STATE_MACHINE.md` §1.

Fault identity and the graph property are independent. REPORT_READY is a
*normal* phase that is absorbing, and TECHNICAL_LOSS is a fault that is **not**
absorbing: it hands the sub-game to SUBGAME_COMPLETE. Use
:attr:`ProtocolMachine.is_absorbing` for "has no successor"; this tuple means
"is a fault".
"""

NORMAL_PHASES: Final[tuple[ProtocolPhase, ...]] = tuple(
    phase for phase in _ALLOWED if phase not in FAULT_PHASES
)
"""The 15 normal lifecycle phases, in `STATE_MACHINE.md` §2 table order."""


@dataclass(frozen=True, slots=True)
class ProtocolMachine:
    """An immutable holder of the current phase.

    The constructor is a **trusted snapshot primitive**: it accepts any valid
    phase so a caller that already holds one can wrap it. It is *not* the
    untrusted runtime API - normal bootstrap goes through :meth:`start`, which
    begins at BOOT ("entry condition: process start"), and every later phase is
    reached only through :meth:`advance`.
    """

    phase: ProtocolPhase

    def __post_init__(self) -> None:
        if not isinstance(self.phase, ProtocolPhase):
            raise IllegalTransitionError(
                f"phase must be a ProtocolPhase, got {type(self.phase).__name__}",
            )

    @classmethod
    def start(cls) -> "ProtocolMachine":
        """Return the normal initial machine, at BOOT."""
        return cls(ProtocolPhase.BOOT)

    @property
    def is_absorbing(self) -> bool:
        """Return True when the frozen graph names no successor for this phase."""
        return _ALLOWED[self.phase] == ()

    def allowed_next(self) -> tuple[ProtocolPhase, ...]:
        """Return the legal successors, in the frozen table's order."""
        return _ALLOWED[self.phase]

    def advance(self, target: ProtocolPhase) -> "ProtocolMachine":
        """Return a new machine in *target*, or raise if that step is illegal."""
        if not isinstance(target, ProtocolPhase):
            raise IllegalTransitionError(
                f"target must be a ProtocolPhase, got {type(target).__name__}",
            )
        if target not in _ALLOWED[self.phase]:
            raise IllegalTransitionError(
                f"illegal transition {self.phase.value} -> {target.value}",
            )
        return ProtocolMachine(target)
