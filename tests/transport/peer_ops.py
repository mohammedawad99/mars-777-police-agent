"""A recording `PeerOperations` and the semantic fixtures the transport carries.

The fake records what the **application** received - the only way to separate
"the wire accepted it" from "the runtime got the right semantic value".
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
from mars777_police.protocol.config_lock import ConfigLockAuthenticator, config_sha256
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator
from mars777_police.transport.handlers import AuditDocument

RESULT_DIGEST = Sha256Digest("c" * 64)
CURSOR = TurnCursor(1, 1)
COMMIT_DIGEST = Sha256Digest("a" * 64)
ILLEGAL_HINT = "illegal"


def authenticator() -> KeyedAuthenticator:
    """The provisioned keyed authenticator both fixtures share."""
    return KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    )


def step0_exchange(vram: int | None = None) -> Step0DeclarationExchange:
    """A peer's Step-0 exchange; `vram=None` is the CPU-only branch."""
    declaration = partial(GROUP_B, COMMIT_B, "group_b", vram=vram)
    return Step0Runtime(GROUP_B, Step0Authenticator(authenticator())).outbound(declaration)


def proposal() -> ConfigProposal:
    """A complete config proposal carrying the two FIXED decimals."""
    return ConfigProposal(1, config(), PROFILES)


def lock_evidence() -> ConfigLockEvidence:
    """Authenticated lock evidence over the locally computed digest."""
    context = ConfigLockContext(GAME_ID, GAME_UID, 1, config_sha256(config()), PROFILES)
    return ConfigLockEvidence(context, ConfigLockAuthenticator(authenticator()).prove(context))


def commitment() -> Commitment:
    """One sealed commitment."""
    return Commitment(CURSOR, COMMIT_DIGEST)


def acknowledgement() -> Acknowledgement:
    """The acknowledgement echoing that commitment."""
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


class RecordingOperations:
    """Records the semantic values the application layer actually received."""

    def __init__(self) -> None:
        self.seen: list[tuple[str, object]] = []
        self.failure: BaseException | None = None

    def _record(self, name: str, value: object) -> None:
        if self.failure is not None:
            raise self.failure
        self.seen.append((name, value))

    def kinds(self) -> list[str]:
        """The operation names invoked, in order."""
        return [name for name, _ in self.seen]

    def on_step0(self, exchange: Step0DeclarationExchange) -> None:
        self._record("step0", exchange)

    def on_config_proposal(self, value: ConfigProposal) -> None:
        self._record("config_proposal", value)

    def on_config_lock(self, value: ConfigLockEvidence) -> None:
        self._record("config_lock", value)

    def on_commitment(self, value: Commitment) -> None:
        self._record("commitment", value)

    def on_acknowledgement(self, value: Acknowledgement) -> None:
        self._record("acknowledgement", value)

    def on_reveal(self, value: Reveal) -> bool:
        self._record("reveal", value)
        return value.hint != ILLEGAL_HINT

    def on_final_nonce_reveal(self, value: FinalNonceReveal) -> None:
        self._record("final_nonce_reveal", value)

    def on_audit_disclosure(self, value: AuditDocument) -> None:
        self._record("audit_disclosure", value)

    def on_result_agreement(self, value: ResultAgreement) -> Sha256Digest:
        self._record("result_agreement", value)
        return RESULT_DIGEST
