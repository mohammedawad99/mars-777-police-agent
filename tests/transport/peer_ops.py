"""A recording `PeerOperations` and the semantic fixtures the transport carries.

The fake records what the **application** received - the only way to separate
"the wire accepted it" from "the runtime got the right semantic value". It takes
the Stage-5-R3R session and ignores it: the gate is proved against production.
"""

from r16_builders import (
    COMMIT_B,
    GAME_ID,
    GAME_UID,
    GROUP_B,
    KEY_ID,
    PROFILES,
    SHARED_KEY,
    config,
    contribution,
    partial,
)

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.peer_final_messages import (
    FinalNonceReveal,
    NonceRevealEntry,
    ResultAgreement,
)
from mars777_police.app.peer_pregame_messages import (
    ConfigLockContext,
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)
from mars777_police.app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.config_lock import ConfigLockAuthenticator, config_sha256
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator
from mars777_police.protocol.scent_model import scent_model_sha256
from mars777_police.transport.handlers import AuditDocument

RESULT_DIGEST, COMMIT_DIGEST = Sha256Digest("c" * 64), Sha256Digest("a" * 64)
CURSOR = TurnCursor(1, 1)
ILLEGAL_HINT = "illegal"


def authenticator() -> KeyedAuthenticator:
    """The provisioned keyed authenticator both fixtures share."""
    return KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    )


def step0_exchange(vram: int | None = None) -> Step0DeclarationExchange:
    """A peer's Step-0 exchange; `vram=None` is the CPU-only branch."""
    declaration = partial(GROUP_B, COMMIT_B, vram=vram)
    return Step0Runtime(GROUP_B, Step0Authenticator(authenticator())).outbound(declaration)


def proposal() -> ConfigProposal:
    """A complete config proposal carrying the two FIXED decimals."""
    return ConfigProposal(1, config(), PROFILES, default_scent_model())


def lock_evidence() -> ConfigLockEvidence:
    """Authenticated lock evidence over the locally computed digest."""
    context = ConfigLockContext(
        GAME_ID,
        GAME_UID,
        1,
        config_sha256(config()),
        PROFILES,
        scent_model_sha256(default_scent_model()),
    )
    return ConfigLockEvidence(context, ConfigLockAuthenticator(authenticator()).prove(context))


def commitment() -> Commitment:
    """One sealed commitment."""
    return Commitment(CURSOR, COMMIT_DIGEST)


def acknowledgement() -> Acknowledgement:
    """The acknowledgement echoing it."""
    return Acknowledgement(CURSOR, COMMIT_DIGEST)


def reveal(hint: str = "north please") -> Reveal:
    """A reveal; the fake calls it illegal when the hint says so."""
    return Reveal(CURSOR, MoveAction(Move.N), hint)


def final_nonce() -> FinalNonceReveal:
    """The batched nonce disclosure."""
    return FinalNonceReveal((NonceRevealEntry(CURSOR, NonceValue("0" * 32)),))


def audit_document() -> AuditDocument:
    """A JSON-native disclosure document - no path, URL, base64 or pickle."""
    return {"sub_game": 1, "entries": [{"step": 1, "verified": True}]}


def agreement() -> ResultAgreement:
    """The peer's single result agreement."""
    from r16_builders import DECLARATION_REF, STAMP

    return ResultAgreement(
        GAME_ID, GAME_UID, DECLARATION_REF, STAMP, contribution(GROUP_B, COMMIT_B)
    )
