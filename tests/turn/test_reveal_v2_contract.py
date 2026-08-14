"""The V2 turn contract: one emission on the reveal, and nothing else moved.

`..._SCENT_V2` is a *new* posture rather than a redefinition of V1, so both
tokens still exist and each still means what it named. A session speaks exactly
one of them, and a reveal that contradicts the one it speaks is refused as a
malformed message - the postures were compared before `CONFIG_LOCKED`, so this is
a broken encoder, never a game event.

What the receiver keeps is the peer's own claim about what it deposited. It is
not recomputed, not checked against an opponent position nobody holds, and not
folded into any field: a full turn is two half-turns, and whoever decays the
world will know when one has completed.
"""

import dataclasses

import pytest
import turn_builders as build
from turn_builders import START, advanced, commitment, legal_reveal, runtime

from mars777_police.app.interop_profiles import COUNTED_TURN_PROFILE, CompatibilityProfile
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.app.protocol_values import NonceValue
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_scent_contract import SCENT_POSTURE, require_scent_shape
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move
from mars777_police.protocol.commitment import build_sealed_record

V1 = CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_V1


def v1_runtime() -> object:
    """A live runtime whose session negotiated the legacy V1 posture."""
    return dataclasses.replace(runtime(), posture=V1)


def test_the_fifth_posture_exists_with_its_exact_token() -> None:
    assert SCENT_POSTURE.value == "STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2"
    assert SCENT_POSTURE.value == COUNTED_TURN_PROFILE
    assert len(CompatibilityProfile) == 5


def test_the_four_earlier_postures_survive_unchanged() -> None:
    """V2 is added beside them; none is deleted or reinterpreted."""
    assert [member.value for member in CompatibilityProfile] == [
        "STRICT_COUNTED_MATCH",
        "STRICT_COUNTED_MATCH_TURN_OUTCOME_V1",
        "STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2",
        "LECTURER_REFERENCE_COMPATIBILITY",
        "LECTURER_ATTACHMENT_COMPATIBILITY",
    ]


def test_the_reveal_carries_exactly_five_members() -> None:
    names = tuple(field.name for field in dataclasses.fields(Reveal))
    assert names == ("cursor", "action", "hint", "capture_claim", "scent_emission")


def test_a_v1_reveal_still_constructs_and_carries_no_emission() -> None:
    """Legacy parseability: the fifth member is optional at the value level."""
    legacy = Reveal(START, MoveAction(Move.N), "heading north")
    assert legacy.scent_emission is None and legacy.capture_claim is None


def test_the_emission_must_be_the_frozen_semantic_type() -> None:
    with pytest.raises(ValueError, match="scent_emission must be a ScentEmission"):
        Reveal(START, MoveAction(Move.N), "north", None, [(1, 1)])  # type: ignore[arg-type]


def test_the_sealed_commitment_is_still_exactly_eight_members() -> None:
    """Neither adjunct is sealed: `H_commit` covers the same eight it always did."""
    sealed = SealedState(build.PEER_DIGEST, build.CENTRE, (), 1, ActorRole.POLICE)
    record = build_sealed_record(
        state=sealed,
        action=MoveAction(Move.N),
        intent=Intent.TRUTH,
        hint="north",
        cursor=START,
        role=ActorRole.POLICE,
        nonce=NonceValue("0" * 32),
    )
    assert len(record) == 8
    assert "scent_emission" not in record and "capture_claim" not in record


def test_a_v2_session_refuses_a_reveal_with_no_emission() -> None:
    live = advanced(runtime())
    with pytest.raises(MalformedMessageError, match="requires a scent emission"):
        live.accept_reveal(Reveal(START, MoveAction(Move.N), "north"))


def test_a_v1_session_refuses_a_reveal_that_smuggles_one() -> None:
    """Profile smuggling: V2 data must not be consumed under a V1 session."""
    legacy = advanced(v1_runtime())  # type: ignore[arg-type]
    with pytest.raises(MalformedMessageError, match="carries no scent emission"):
        legacy.accept_reveal(legal_reveal())


def test_a_v1_session_accepts_the_legacy_shape_it_negotiated() -> None:
    legacy = advanced(v1_runtime())  # type: ignore[arg-type]
    outcome = legacy.accept_reveal(Reveal(START, MoveAction(Move.N), "north"))
    assert outcome.accepted is True


@pytest.mark.parametrize(
    "posture",
    [
        CompatibilityProfile.STRICT_COUNTED_MATCH,
        CompatibilityProfile.LECTURER_REFERENCE_COMPATIBILITY,
        CompatibilityProfile.LECTURER_ATTACHMENT_COMPATIBILITY,
    ],
)
def test_no_other_posture_silently_accepts_v2_data(posture: CompatibilityProfile) -> None:
    with pytest.raises(MalformedMessageError, match="carries no scent emission"):
        require_scent_shape(legal_reveal(), posture)


def test_the_receiver_retains_the_peer_emission_against_its_own_cursor() -> None:
    live = advanced(runtime())
    reveal = legal_reveal()
    live.accept_reveal(reveal)
    (witnessed,) = live.evidence
    assert witnessed.scent is reveal.scent_emission
    assert witnessed.cursor == START and witnessed.h_commit == commitment().h_commit


def test_the_retained_emission_is_the_peers_and_never_our_own() -> None:
    """Our outgoing scent is what we send; it is not opponent observation."""
    live = advanced(runtime())
    ours = build.emission(build.CENTRE)
    theirs = build.emission(build.BLOCKED)
    assert ours != theirs
    live.accept_reveal(Reveal(START, MoveAction(Move.N), "north", None, theirs))
    (witnessed,) = live.evidence
    assert witnessed.scent == theirs and witnessed.scent != ours


def test_the_receiver_builds_no_opponent_truth_and_decays_nothing() -> None:
    """One reveal is half a turn: no field, no decay, no opponent position."""
    live = advanced(runtime())
    before = live.truth
    live.accept_reveal(legal_reveal())
    assert live.truth == before, "the peer's action never moves our own piece"
    assert not hasattr(live, "peer_truth") and not hasattr(live, "opponent_field")
    assert not any(hasattr(one, "field") for one in live.evidence)
