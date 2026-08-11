"""Codec for the config proposal and the config lock evidence.

Split from `codec_declaration` by family: the declaration tree there, the two
config-bearing pregame families here. Both reuse `codec_auth` for the envelope
and `codec_config` for the 35-member core, so no value has two encoders.
"""

from ..app.peer_pregame_messages import ConfigLockContext, ConfigLockEvidence, ConfigProposal
from ..app.protocol_values import Sha256Digest
from .codec_auth import decode_auth, decode_profiles, encode_auth, encode_profiles
from .codec_config import decode_config, encode_config
from .wire_config import (
    ConfigLockContextWire,
    ConfigLockEvidenceWire,
    ConfigProposalWire,
)


def decode_proposal(wire: ConfigProposalWire) -> ConfigProposal:
    """Rebuild a complete config proposal - never a delta."""
    return ConfigProposal(wire.sub_game, decode_config(wire.config), decode_profiles(wire.profiles))


def encode_proposal(proposal: ConfigProposal) -> ConfigProposalWire:
    """Render a complete config proposal."""
    return ConfigProposalWire(
        sub_game=proposal.sub_game,
        config=encode_config(proposal.config),
        profiles=encode_profiles(proposal.profiles),
    )


def decode_lock(wire: ConfigLockEvidenceWire) -> ConfigLockEvidence:
    """Rebuild lock evidence; the proof stays outside the context it covers."""
    context = wire.context
    return ConfigLockEvidence(
        ConfigLockContext(
            context.game_id,
            context.game_uid,
            context.sub_game,
            Sha256Digest(context.config_sha256),
            decode_profiles(context.profiles),
        ),
        decode_auth(wire.auth),
    )


def encode_lock(evidence: ConfigLockEvidence) -> ConfigLockEvidenceWire:
    """Render lock evidence."""
    context = evidence.context
    return ConfigLockEvidenceWire(
        context=ConfigLockContextWire(
            game_id=context.game_id,
            game_uid=context.game_uid,
            sub_game=context.sub_game,
            config_sha256=context.config_sha256.value,
            profiles=encode_profiles(context.profiles),
        ),
        auth=encode_auth(evidence.auth),
    )
