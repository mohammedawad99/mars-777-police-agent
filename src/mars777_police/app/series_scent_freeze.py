"""One scent model, held for the whole six-sub-game series.

SCENT-001 wants the agreed model locked **before the series**, and the layers
below already do their half: the codec refuses a model our physics rejects,
strict agreement refuses a valid model that is not ours, and the config lock
authenticates the digest of the model each sub-game actually locked. All three
are per-sub-game questions. None of them stops `g01` locking one model and `g02`
locking a different one that both sides equally agreed - which is a *series*
question, and this value is its answer.

**The digest is the model.** The full descriptor was exchanged and compared
before the lock, and the digest was then bound into the authenticated lock
context, so for continuity there is nothing left to keep but the identity. No
second kernel, no second canonicalization, no second proof.

**Immutable by construction.** `established` never mutates: it returns the
freeze a series holds *after* a sub-game locked a model, which is a new frozen
value for the first one, the unchanged value for a repeat of the same one, and a
refusal for any other - so a mid-series switch cannot overwrite what `g01` set
even by accident. Ordering is not decided here either: the freeze belongs to
whichever sub-game the existing series cursor let lock first, and duplicating
that cursor rule would create a second authority for it.
"""

from dataclasses import dataclass

from .protocol_errors import ConfigMismatchError, LocalDefectError
from .protocol_values import Sha256Digest


@dataclass(frozen=True, slots=True)
class SeriesScentFreeze:
    """The scent-model identity this series is committed to, once it has one."""

    identity: Sha256Digest | None = None
    """Unset until a sub-game of this series completed a verified config lock."""

    def __post_init__(self) -> None:
        if self.identity is not None and not isinstance(self.identity, Sha256Digest):
            raise LocalDefectError(
                "a frozen scent-model identity must be a Sha256Digest,"
                f" got {type(self.identity).__name__}",
            )

    def established(self, locked: Sha256Digest) -> "SeriesScentFreeze":
        """Return this series' freeze after a sub-game verifiably locked *locked*.

        A mismatch is a pregame refusal (`E-CONFIG-MISMATCH`): an agreed term
        changed before play, which is neither tampering nor a game event.
        """
        if self.identity is None:
            return SeriesScentFreeze(locked)
        if locked != self.identity:
            raise ConfigMismatchError(
                "this series already locked its scent model; a later sub-game may not"
                " change the agreed model, however validly both sides agreed"
                " and authenticated the new one",
            )
        return self
