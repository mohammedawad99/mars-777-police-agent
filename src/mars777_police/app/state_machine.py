"""The frozen protocol phase machine and its transition evidence.

Sole authority on what may happen next; owns one fact, the current phase
(`MODULE_BOUNDARIES.md`, `STATE_OWNERSHIP.md`). Phase ORDER only: COMMIT_SENT,
ACKNOWLEDGED, REVEAL and FINAL_AUDIT are labels with no cryptography, message
body or transport, and the caller supplies the target phase. Per R7 and
`PROTOCOL_TIMELINE.md` event 10 - a "phase transition", persistence and hashing
both "-" - evidence is the two phases and nothing else; `infra.logger` owns
persistence and the official log artifact is a separate contract. ``_ALLOWED``
is the single authoritative graph from `STATE_MACHINE.md` §2, including the
Stage-4A-FIX1 correction ``TECHNICAL_LOSS -> SUBGAME_COMPLETE``.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class IllegalTransitionError(Exception):
    """Illegal phase step; outer layers map it to E-PROTO-STALE / E-LOCAL-DEFECT."""


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
"""The 3 "terminal / fault" phases; independent of :attr:`ProtocolMachine.is_absorbing`."""

NORMAL_PHASES: Final[tuple[ProtocolPhase, ...]] = tuple(
    phase for phase in _ALLOWED if phase not in FAULT_PHASES
)
"""The 15 normal lifecycle phases, in `STATE_MACHINE.md` §2 table order."""


def _require_phase(value: object, name: str) -> ProtocolPhase:
    if not isinstance(value, ProtocolPhase):
        raise IllegalTransitionError(f"{name} must be a ProtocolPhase, got {type(value).__name__}")
    return value


@dataclass(frozen=True, slots=True)
class TransitionEvidence:
    """Replayable record of one SUCCESSFUL transition: the two phases only.

    Valid by construction - the pair must be an edge of ``_ALLOWED``, the sole
    graph - since a record of a forbidden step (R1, R5) is untruthful. Validity
    is not authenticity: a well-formed edge is never proof that it occurred.
    """

    source_phase: ProtocolPhase
    target_phase: ProtocolPhase

    def __post_init__(self) -> None:
        source = _require_phase(self.source_phase, "source_phase")
        target = _require_phase(self.target_phase, "target_phase")
        if target not in _ALLOWED[source]:
            raise IllegalTransitionError(
                f"illegal transition {source.value} -> {target.value}",
            )


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """A successful transition: the new machine and its evidence."""

    machine: "ProtocolMachine"
    evidence: TransitionEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, TransitionEvidence):
            raise IllegalTransitionError("result needs a TransitionEvidence")
        if self.evidence.target_phase is not self.machine.phase:
            raise IllegalTransitionError(
                f"evidence target {self.evidence.target_phase.value} does not match"
                f" machine phase {self.machine.phase.value}",
            )


@dataclass(frozen=True, slots=True)
class ProtocolMachine:
    """Immutable current phase; the constructor is a trusted snapshot primitive,
    not the untrusted runtime API - normal bootstrap is :meth:`start` at BOOT."""

    phase: ProtocolPhase

    def __post_init__(self) -> None:
        _require_phase(self.phase, "phase")

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

    def advance(self, target: ProtocolPhase) -> TransitionResult:
        """New machine plus evidence; legality decided once, in TransitionEvidence."""
        evidence = TransitionEvidence(self.phase, _require_phase(target, "target"))
        return TransitionResult(ProtocolMachine(evidence.target_phase), evidence)
