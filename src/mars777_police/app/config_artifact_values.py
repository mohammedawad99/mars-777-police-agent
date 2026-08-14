"""What one config artifact contains, once it is a value rather than bytes.

The config file is the only artifact that reports **two** agreed things and the
one authenticated context that binds them, so reading it back yields four
members rather than a config. They are kept together because they are only
evidence together: a model without the digest beside it proves nothing, and a
digest without the lock context proves nothing about this sub-game.

Representation only. Nothing here parses, hashes or verifies - `transport`
decodes the bytes into these values and `artifact_verification` holds them to
each other.
"""

from dataclasses import dataclass

from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent_model import ScentModelAgreement
from .peer_pregame_messages import ConfigLockEvidence
from .protocol_values import Sha256Digest


@dataclass(frozen=True, slots=True)
class ConfigArtifactContent:
    """The 35-member core, the agreed model, its stored identity and the lock."""

    config: NegotiatedConfig
    scent_model: ScentModelAgreement
    scent_model_sha256: Sha256Digest
    """The digest **as stored**, never as recomputed - comparing them is the point."""

    evidence: ConfigLockEvidence
