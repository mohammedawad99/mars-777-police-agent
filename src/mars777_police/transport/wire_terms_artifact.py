"""The config artifact as the reference wire can actually evidence it.

`ConfigArtifactWire` records a sub-game's configuration with the keyed lock our
own counted path performs. The opponent's runner performs no such lock, and the
book requires none: `config_sha256` is defined there as the canonical hash of
the agreed terms, and the only mandatory signed artifact is the report. So a
second envelope exists for the provenance the proven wire does carry.

**Three layers, exactly as `CONFIG_CONTRACT.md` §R12-E keeps them**, and for the
same reason: `config` is byte-for-byte what both peers digest, and the digest,
the agreement and the model sit outside it rather than inside the bytes they
cover. Only the middle layer differs from the keyed form - a nonce and the
digest it bound, instead of a proof and its key label.

**The section is named for what it is.** `terms_agreement`, never `config_lock`:
a reader must not have to know the difference between an unkeyed digest anyone
can recompute and a keyed proof only the key holder can produce. The name says
which one this file holds.

**The frozen profile set is deliberately absent.** A lock context records it
because the counted wire negotiates it; the reference wire does not, and our
selection of `KIT_CORE_COMMITMENT_V1` has no representation in that profile wire
at all - the encoder refuses it by design. Writing our own local selection into
the record would state an agreement neither side ever made. What the two sides
did agree is here: the identity, the sub-game, and the two digests.

Strict like every other wire model here: an unknown member is refused rather
than ignored.
"""

from pydantic import BaseModel

from .wire_artifacts import ScentModelEvidenceWire
from .wire_config import NegotiatedConfigWire
from .wire_config_sections import WIRE
from .wire_scalars import DigestText


class TermsContextWire(BaseModel):
    """What the reference wire actually bound: identity, sub-game, two digests."""

    model_config = WIRE

    game_id: str
    game_uid: str
    sub_game: int
    config_sha256: DigestText
    scent_model_sha256: DigestText


class TermsAgreementWire(BaseModel):
    """The nonce that bound this sub-game's terms, and the digest over both."""

    model_config = WIRE

    context: TermsContextWire
    nonce: str
    terms_signature: DigestText


class TermsConfigArtifactWire(BaseModel):
    """`config_<game_id>_g<NN>.json`, evidenced by agreement rather than a key."""

    model_config = WIRE

    config: NegotiatedConfigWire
    terms_agreement: TermsAgreementWire
    scent_model_evidence: ScentModelEvidenceWire
