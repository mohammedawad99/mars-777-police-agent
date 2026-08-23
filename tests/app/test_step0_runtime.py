"""Step-0 outbound and inbound: what we sign, and what we refuse to believe.

Every rejection below is a *comparison against something we already hold*, and
every one refuses rather than repairs. A pre-play failure means counted play
does not start; it never manufactures a technical loss, which is a counted-play
sanction.
"""

import pytest
from r16_builders import (
    COMMIT_A,
    COMMIT_B,
    GROUP_A,
    GROUP_B,
    KEY_ID,
    SHARED_KEY,
    merged,
    partial,
)

from mars777_police.app.auth_values import AuthProfile, AuthProof
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    LocalDefectError,
    StaleMessageError,
)
from mars777_police.app.step0_runtime import Step0Runtime, merge, sole_subtree
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator


def port() -> Step0Authenticator:
    return Step0Authenticator(
        KeyedAuthenticator(
            AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )
    )


def peers() -> tuple[Step0Runtime, Step0Runtime]:
    shared = port()
    return Step0Runtime(GROUP_A, shared), Step0Runtime(GROUP_B, shared)


LOCAL = partial(GROUP_A, COMMIT_A)
PEER = partial(GROUP_B, COMMIT_B)


def test_our_outbound_carries_our_own_snapshot_and_a_verifying_proof() -> None:
    ours, _ = peers()
    exchange = ours.outbound(LOCAL)
    assert exchange.declaration is LOCAL
    assert port().verify(LOCAL, GROUP_A, exchange.auth)


def test_we_refuse_to_sign_a_snapshot_that_is_not_ours() -> None:
    ours, _ = peers()
    with pytest.raises(LocalDefectError):
        ours.outbound(PEER)


def test_we_refuse_to_sign_a_snapshot_carrying_both_subtrees() -> None:
    ours, _ = peers()
    with pytest.raises(StaleMessageError):
        ours.outbound(merged())


def test_a_valid_exchange_produces_a_merged_snapshot_both_sides_agree_on() -> None:
    ours, theirs = peers()
    ours_merged = ours.accept(LOCAL, theirs.outbound(PEER))
    theirs_merged = theirs.accept(PEER, ours.outbound(LOCAL))
    assert ours_merged == theirs_merged == merged()
    assert ours_merged.teams.is_merged


def test_neither_input_snapshot_is_mutated_by_the_merge() -> None:
    ours, theirs = peers()
    before_local, before_peer = LOCAL, PEER
    ours.accept(LOCAL, theirs.outbound(PEER))
    assert LOCAL is before_local and LOCAL.teams.group_a is None
    assert PEER is before_peer and PEER.teams.group_b is None


def test_a_peer_may_not_author_our_own_subtree() -> None:
    ours, _ = peers()
    forged = Step0Runtime(GROUP_A, port()).outbound(LOCAL)
    with pytest.raises(StaleMessageError):
        ours.accept(LOCAL, forged)


def test_two_snapshots_claiming_the_same_slot_are_refused() -> None:
    """The slot is passed explicitly here because the wrong layout *is* the case.

    Left to derive, the peer would seat itself correctly and there would be no
    collision to refuse; forcing it into the slot we already occupy is what a
    mis-implemented peer would actually send.
    """
    ours = sole_subtree(LOCAL)[0]
    with pytest.raises(StaleMessageError):
        merge(LOCAL, partial(GROUP_B, COMMIT_B, ours))


@pytest.mark.parametrize("field", ["game_id", "game_uid"])
def test_a_different_game_is_stale_not_negotiable(field: str) -> None:
    from dataclasses import replace

    ours, theirs = peers()
    other = replace(PEER, **{field: "another-game"})
    with pytest.raises(StaleMessageError):
        ours.accept(LOCAL, theirs.outbound(other))


def test_a_differing_game_start_refuses_counted_play() -> None:
    from dataclasses import replace

    from mars777_police.app.artifact_values import UtcTimestamp
    from mars777_police.app.declaration_values import DeclarationTimes

    ours, theirs = peers()
    other = replace(PEER, times=DeclarationTimes(UtcTimestamp("2026-08-08T00:00:00Z"), None))
    with pytest.raises(ConfigMismatchError):
        ours.accept(LOCAL, theirs.outbound(other))


def test_a_differing_token_cap_is_a_mismatch_never_an_offer() -> None:
    from dataclasses import replace

    ours, theirs = peers()
    other = replace(PEER, token_budget_per_series=199999)
    with pytest.raises(ConfigMismatchError) as failure:
        ours.accept(LOCAL, theirs.outbound(other))
    assert failure.value.error_id == "E-CONFIG-MISMATCH"


def test_an_unverifiable_proof_fails_closed() -> None:
    ours, theirs = peers()
    exchange = theirs.outbound(PEER)
    forged = AuthProof(exchange.auth.profile, exchange.auth.key_id, "0" * 64)
    with pytest.raises(AuthFailureError):
        ours.accept(LOCAL, type(exchange)(exchange.declaration, forged))


def test_sole_subtree_reports_the_populated_slot() -> None:
    assert sole_subtree(LOCAL)[0] == "group_b"
    assert sole_subtree(PEER)[0] == "group_a"
