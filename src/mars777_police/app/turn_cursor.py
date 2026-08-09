"""The shared turn identity carried by every turn-scoped peer message.

Extracted from `app.peer_messages` at Stage 4E-R7 because **both** message
modules need it and neither should import the other: `app.peer_turn_messages`
carries it today and `app.peer_final_messages` will carry it in a batched final
reveal. Keeping it here leaves that dependency symmetric and the graph acyclic.
The value itself is unchanged - this was a move, not a redesign.
"""

from dataclasses import dataclass

from ..domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES


@dataclass(frozen=True, slots=True)
class TurnCursor:
    """The transmitted identity of one turn-scoped message.

    Exactly ``(sub_game, step)`` (PRD-02 §8; PRD02-FR-044/FR-063). **No phase**:
    the receiver owns the single authoritative ``ProtocolMachine`` and checks
    admissibility against it (FR-021/FR-062, STATE-003), so a transmitted phase
    would duplicate that authority or be uncomputable in lockstep. A
    *projection*, never an owner - the sub-game index belongs to
    ``app.orchestrator``, the step to ``domain.truth`` - validation is
    **structural only**: ``sub_game`` reads the one globally FIXED ``num_games``
    authority rather than restating six, while ``step`` has no context-free
    ceiling because ``max_moves`` is per-sub-game locked config it never carries.
    """

    sub_game: int
    step: int

    def __post_init__(self) -> None:
        _require_int(self.sub_game, "sub_game")
        _require_int(self.step, "step")
        if not FIRST_SUB_GAME <= self.sub_game <= FIXED_NUM_GAMES:
            raise ValueError(
                f"sub_game must be in [{FIRST_SUB_GAME}, {FIXED_NUM_GAMES}], got {self.sub_game}",
            )
        if self.step < 1:
            raise ValueError(f"step must be at least 1, got {self.step}")


def _require_int(value: object, name: str) -> None:
    """Reject anything but a real ``int``; ``bool`` is an ``int`` and is refused.

    Accepting ``True`` as sub-game 1 would be exactly the silent coercion the
    project forbids, so the check is on the type itself, not ``isinstance``.
    """
    if type(value) is not int:
        raise ValueError(f"{name} must be an int, got {type(value).__name__}")
