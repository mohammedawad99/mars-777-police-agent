"""The scent model's **external** registration identity, and what it is not.

Two peers running different code must agree on one pheromone physics. They do,
and they proved it member by member - but they cannot agree on a single digest
of it, because the opponent's registration document records its own IEEE-754
accumulation (`raw: 1.4300000000000002`) and our physics is exact `Decimal`. Two
honest implementations of the same recurrence therefore hash to different
numbers, and a peer that recomputed our digest from its own bytes would refuse a
model it actually agrees with.

So the identity that crosses the wire is the **registration** the pairing agreed
out of band - a name and the digest of the opponent's own document - preserved
exactly as agreed and never re-derived here. What *is* checked locally is the
thing a digest could never prove anyway: that the physics the contract froze is
the physics this process implements. A registration naming values we do not play
is refused before a sub-game opens, because playing under a name we contradict
is worse than refusing to play.

Our internal model keeps its own separate identity
(`protocol.scent_model.scent_model_sha256`) over our own canonical form. The two
digests are different domains and neither substitutes for the other; conflating
them is the mistake this module exists to make unavailable.
"""

from dataclasses import dataclass
from decimal import Decimal

from ..domain.scent_model import ScentModelAgreement
from ..infra.game_contract import scent_parameters, scent_registration
from .protocol_errors import LocalDefectError

FAMILY = "scent_model"
"""The lock family this registration is declared under on the KIT greeting."""


@dataclass(frozen=True, slots=True)
class ScentRegistration:
    """One agreed model's external name and registration digest."""

    model_id: str
    registration_sha256: str

    def __post_init__(self) -> None:
        if not self.model_id:
            raise LocalDefectError("a scent registration names no model")
        digest = self.registration_sha256
        if len(digest) != 64 or digest.lower() != digest or not _is_hex(digest):
            raise LocalDefectError(
                f"a registration digest is 64 lowercase hex characters, got {digest!r}",
            )


def _is_hex(value: str) -> bool:
    return all(character in "0123456789abcdef" for character in value)


def registered_model(model: ScentModelAgreement) -> ScentRegistration:
    """The agreed registration, or a refusal naming the value that disagrees.

    Fail-closed by construction: every FIXED value the contract froze is compared
    against the model this process will actually run, and a mismatch raises
    rather than degrading to an undeclared greeting. A silent fallback here would
    mean playing a physics the pairing did not agree while declaring one it did.
    """
    centre, decay, size = scent_parameters()
    for name, agreed, ours in (
        ("pheromone_center_intensity", Decimal(centre), model.center_intensity),
        ("pheromone_decay", Decimal(decay), model.decay_rate),
        ("pheromone_grid_size", Decimal(size), Decimal(model.field_size)),
    ):
        if agreed != ours:
            raise LocalDefectError(
                f"the shared contract froze {name}={agreed} and this process plays"
                f" {ours}; a registration must not name physics we contradict",
            )
    model_id, digest = scent_registration()
    return ScentRegistration(model_id, digest)
