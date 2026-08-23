"""Mapping the config artifact between its stored JSON and its semantic value.

Mapping only, in both directions, and no evidence check of its own: whether the
stored digest really covers the stored model, and whether the proof verifies, is
`artifact_verification`'s decision over these values. What happens here is the
same thing every other codec does - the strict schema refuses a shape nobody
froze, the existing decoders rebuild the semantic values, and whatever they
refuse becomes this layer's malformed identity.

`decode_scent_model` is deliberately reused rather than repeated: a stored model
that the project's own physics would refuse never becomes a value at all.
"""

from collections.abc import Mapping

from pydantic import ValidationError

from ..app.config_artifact_values import ConfigArtifactContent, TermsConfigArtifactContent
from ..app.protocol_errors import MalformedMessageError
from ..app.protocol_values import Sha256Digest
from .codec_config import decode_config, encode_config
from .codec_pregame import decode_lock, encode_lock
from .codec_scent_model import decode_scent_model, encode_scent_model
from .wire_artifacts import ConfigArtifactWire, ScentModelEvidenceWire
from .wire_terms_artifact import (
    TermsAgreementWire,
    TermsConfigArtifactWire,
    TermsContextWire,
)


def read_config_artifact(document: Mapping[str, object]) -> ConfigArtifactWire:
    """Parse *document* as a config artifact, refusing any other shape."""
    try:
        return ConfigArtifactWire.model_validate(dict(document))
    except ValidationError as failure:
        raise MalformedMessageError(f"not a config artifact: {failure}") from None


def decode_config_artifact(document: Mapping[str, object]) -> ConfigArtifactContent:
    """Rebuild what a stored config artifact says, member by member."""
    wire = read_config_artifact(document)
    return ConfigArtifactContent(
        decode_config(wire.config),
        decode_scent_model(wire.scent_model_evidence.model),
        Sha256Digest(wire.scent_model_evidence.scent_model_sha256),
        decode_lock(wire.config_lock),
    )


def encode_config_artifact(content: ConfigArtifactContent) -> ConfigArtifactWire:
    """Render one config artifact - the same schema a reader validates against."""
    return ConfigArtifactWire(
        config=encode_config(content.config),
        config_lock=encode_lock(content.evidence),
        scent_model_evidence=ScentModelEvidenceWire(
            model=encode_scent_model(content.scent_model),
            scent_model_sha256=content.scent_model_sha256.value,
        ),
    )


def encode_terms_config_artifact(
    content: TermsConfigArtifactContent,
) -> TermsConfigArtifactWire:
    """Render one config artifact evidenced by the nonce-bound terms agreement."""
    evidence = content.evidence
    context = evidence.context
    return TermsConfigArtifactWire(
        config=encode_config(content.config),
        terms_agreement=TermsAgreementWire(
            context=TermsContextWire(
                game_id=context.game_id,
                game_uid=context.game_uid,
                sub_game=context.sub_game,
                config_sha256=context.config_sha256.value,
                scent_model_sha256=context.scent_model_sha256.value,
            ),
            nonce=evidence.nonce,
            terms_signature=evidence.terms_signature,
        ),
        scent_model_evidence=ScentModelEvidenceWire(
            model=encode_scent_model(content.scent_model),
            scent_model_sha256=content.scent_model_sha256.value,
        ),
    )
