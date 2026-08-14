"""One turn's scent, as the value the history keeps in either direction.

`scent_emission` is not a member of `H_commit` - like the capture claim it is a
live interaction fact, not a sealed one - so nothing in the cryptography stops a
peer from disclosing a different emission at the final audit than the one it
actually sent. This value is what makes that detectable: each side keeps the
rows it really observed during the authenticated session, and the peer's
disclosure is compared against them row for row.

**Two members, and deliberately no third.** The cursor says which turn, the
emission says what that turn deposited. There is no role, no source cell, no
model, no expected emission and no verdict: the sub-game and the sender are
already identified by the document that carries these rows, where the emitter
stood is sealed until the audit, and whether the emission is *physically* right
is a different question from whether it is the one that was sent.
"""

from dataclasses import dataclass

from ..domain.scent_emission import ScentEmission
from .turn_cursor import TurnCursor


@dataclass(frozen=True, slots=True)
class ScentRecord:
    """One turn's emission, bound to the cursor it belongs to.

    The guards are about *our* construction of a row: a peer's JSON is already
    typed by `audit_scent` before it reaches here, so a bad value at this point
    is a local defect and raises the plain `ValueError` that is.
    """

    cursor: TurnCursor
    emission: ScentEmission

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(
                f"a scent record needs a TurnCursor, got {type(self.cursor).__name__}",
            )
        if type(self.emission) is not ScentEmission:
            raise ValueError(
                f"emission must be a ScentEmission, got {type(self.emission).__name__}",
            )
