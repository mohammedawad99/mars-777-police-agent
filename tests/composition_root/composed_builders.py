"""Two real compositions, built from synthetic settings - no operator env read."""

from evidence_builders import CONFIG
from r16_builders import (
    COMMIT_A,
    COMMIT_B,
    GAME_ID,
    GAME_UID,
    GROUP_A,
    GROUP_B,
    PROFILES,
    config,
    partial,
)

from mars777_police.app.auth_values import KeyId
from mars777_police.app.public_endpoint_values import (
    LocalPeerEndpoint,
    OpponentPublicPeerEndpoint,
)
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.composition import compose_agent
from mars777_police.composition_values import AgentComposition, SeriesIdentity
from mars777_police.infra.settings import AuthSecret, RuntimeSettings

KEY_ID = KeyId("mars777-k1")
SHARED = b"out-of-band-provisioned-secret"
FIRST_SUB_GAME = 1
COMMITS = {GROUP_A: COMMIT_A, GROUP_B: COMMIT_B}
"""Each group's declared repository commit, as the result core checks it."""


def settings_for(role: ActorRole, opponent: str, port: int = 8080) -> RuntimeSettings:
    """Synthetic operator settings; the real environment is never read."""
    return RuntimeSettings(
        role,
        LocalPeerEndpoint("127.0.0.1", port),
        KEY_ID,
        AuthSecret(SHARED),
        OpponentPublicPeerEndpoint(opponent),
    )


def identity_for(group_id: str, slot: str) -> SeriesIdentity:
    """The series facts settings deliberately cannot hold."""
    return SeriesIdentity(
        GAME_ID,
        GAME_UID,
        FIRST_SUB_GAME,
        partial(group_id, COMMITS[group_id], slot),
        PROFILES,
        config().network_and_league.token_budget_per_series,
    )


def compose(
    group_id: str = GROUP_A,
    slot: str = "group_a",
    role: ActorRole = ActorRole.POLICE,
    opponent: str = "https://opponent.example/mcp",
    port: int = 8080,
) -> AgentComposition:
    """One real production agent object graph."""
    return compose_agent(settings_for(role, opponent, port), identity_for(group_id, slot), group_id)


def both(url_a: str, url_b: str) -> tuple[AgentComposition, AgentComposition]:
    """Two compositions pointed at each other's ingress."""
    a = compose(GROUP_A, "group_a", ActorRole.POLICE, url_b)
    b = compose(GROUP_B, "group_b", ActorRole.THIEF, url_a)
    return a, b


def sealed(role: ActorRole) -> object:
    """The own-known snapshot a side seals for step 1."""
    from evidence_builders import POS

    from mars777_police.app.sealed_record_values import SealedState

    return SealedState(CONFIG, POS[1], (), 1, role)


def final_result_inputs() -> dict[str, object]:
    """The values only a finished series knows - never built at startup."""
    import cadence_ops
    from r16_builders import CUMULATIVE, LINES, LINKS

    return {
        "lines": LINES,
        "links": LINKS,
        "cumulative": CUMULATIVE,
        "own": cadence_ops.contribution_for(GROUP_A, 200),
    }


def step0_from(group_id: str, slot: str) -> object:
    """A real Step-0 exchange authored by *group_id*, keyed with the shared key."""
    from peer_ops import authenticator

    from mars777_police.app.step0_runtime import Step0Runtime
    from mars777_police.protocol.declaration import Step0Authenticator

    runtime = Step0Runtime(group_id, Step0Authenticator(authenticator()))
    return runtime.outbound(partial(group_id, COMMITS[group_id], slot))


def after_step0(
    composition: AgentComposition, peer_group: str = GROUP_B, slot: str = "group_b"
) -> AgentComposition:
    """Drive the real Step-0 acceptance so the merged declaration exists."""
    assert composition.pregame.accept_step0(step0_from(peer_group, slot)) == peer_group
    return composition


def final_result_inputs_for(group_id: str) -> dict[str, object]:
    """The same late values, contributed by *group_id*."""
    import cadence_ops
    from r16_builders import CUMULATIVE, LINES, LINKS

    return {
        "lines": LINES,
        "links": LINKS,
        "cumulative": CUMULATIVE,
        "own": cadence_ops.contribution_for(group_id, 100),
    }


def evidence_for(role: ActorRole, sub_game: int = FIRST_SUB_GAME) -> object:
    """A real evidence producer for *role*, so the sealed state agrees with it."""
    from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
    from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
    from mars777_police.protocol.audit_commitment import CommitmentRecomputer
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    return OutboundEvidenceRuntime(
        LocalEvidenceContext(GAME_ID, GAME_UID, sub_game, CONFIG, role),
        SecretsNonceSource(),
        CommitmentRecomputer(),
    )
