"""The config artifact's own envelope: the core, its lock, and the agreed model.

`CONFIG_CONTRACT.md` §R12-E keeps the 35-member core, the unkeyed digest and the
keyed proof in three different layers, so the file keeps them in three different
sections. `config` is byte-for-byte the representation both peers digest; the
digest, the proof and the model sit outside it and never inside the bytes they
cover.

Strict like every other wire model here: an unknown member is refused rather
than ignored, so an artifact that grew a field nobody froze fails to parse
instead of being read as if the field were not there.
"""

from pydantic import BaseModel

from .wire_config import ConfigLockEvidenceWire, NegotiatedConfigWire
from .wire_config_sections import WIRE
from .wire_scalars import DigestText
from .wire_scent_model import ScentModelWire


class ScentModelEvidenceWire(BaseModel):
    """The complete agreed model, and the identity derived from it."""

    model_config = WIRE

    model: ScentModelWire
    scent_model_sha256: DigestText


class ConfigArtifactWire(BaseModel):
    """`config_<game_id>_g<NN>.json` as one strict document."""

    model_config = WIRE

    config: NegotiatedConfigWire
    config_lock: ConfigLockEvidenceWire
    scent_model_evidence: ScentModelEvidenceWire
