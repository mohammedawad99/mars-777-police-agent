"""Sealing our own turn: what comes back, what stays behind, what is refused."""

import dataclasses

import evidence_builders as build
import pytest
from evidence_builders import SUB_GAME, ScriptedNonces, prepare, producer

from mars777_police.app.outbound_evidence_values import (
    EvidencePhase,
    PreparedTurn,
    SealedTurnRecord,
)
from mars777_police.app.peer_turn_messages import Commitment, Reveal
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move


def test_preparation_returns_exactly_a_commitment_and_a_reveal() -> None:
    turn = prepare(producer(), 1)
    assert type(turn) is PreparedTurn
    assert type(turn.commitment) is Commitment and type(turn.reveal) is Reveal
    assert {f.name for f in dataclasses.fields(turn)} == {"commitment", "reveal"}


def test_the_prepared_value_exposes_no_secret_member() -> None:
    """A runner holding this cannot leak the nonce, the state or the intent."""
    turn = prepare(producer(), 1)
    exposed = {f.name for f in dataclasses.fields(turn.reveal)}
    assert exposed == {"cursor", "action", "hint", "capture_claim", "scent_emission"}
    assert not hasattr(turn, "nonce") and not hasattr(turn, "state")
    assert not hasattr(turn.reveal, "nonce") and not hasattr(turn.reveal, "intent")


def test_the_commitment_digest_comes_from_the_production_crypto_seam() -> None:
    """Recomputing the retained record by hand through the port must agree."""
    live = producer()
    turn = prepare(live, 1)
    record = live.records[0]
    assert live.commitments.matches(
        turn.commitment.h_commit,
        live.commitments.recompute(
            state=record.state,
            action=record.action,
            intent=record.intent,
            hint=record.hint,
            cursor=record.cursor,
            role=build.OURS,
            nonce=record.nonce,
        ),
    )


def test_the_nonce_is_retained_privately_and_never_returned() -> None:
    live = producer()
    turn = prepare(live, 1)
    assert type(live.records[0]) is SealedTurnRecord
    assert live.records[0].nonce.value not in repr(turn)


def test_the_same_cursor_cannot_be_prepared_twice() -> None:
    live = producer()
    prepare(live, 1)
    with pytest.raises(LocalDefectError, match="already prepared"):
        prepare(live, 1)


def test_a_repeated_nonce_from_the_source_is_a_local_defect() -> None:
    """No silent regeneration and no retry loop: it fails closed."""
    live = producer(ScriptedNonces(["7" * 32]))
    prepare(live, 1)
    with pytest.raises(LocalDefectError, match="already used"):
        prepare(live, 2)


def test_a_cursor_from_another_sub_game_is_refused() -> None:
    live = producer()
    with pytest.raises(LocalDefectError, match="sub-game"):
        live.prepare_turn(
            state=build.sealed(1),
            action=MoveAction(Move.N),
            intent=Intent.TRUTH,
            hint="north",
            cursor=TurnCursor(SUB_GAME + 1, 1),
        )


def test_a_sealed_state_naming_another_role_is_refused() -> None:
    """Role is semantic context, checked - never branched on."""
    live = producer()
    foreign = SealedState(build.CONFIG, build.POS[1], (), 1, ActorRole.POLICE)
    with pytest.raises(LocalDefectError, match="not our own"):
        live.prepare_turn(
            state=foreign,
            action=MoveAction(Move.N),
            intent=Intent.TRUTH,
            hint="north",
            cursor=TurnCursor(SUB_GAME, 1),
        )


def test_a_fresh_runtime_is_open_and_holds_nothing() -> None:
    live = producer()
    assert live.phase is EvidencePhase.OPEN and live.records == ()


def test_the_produced_commitment_is_accepted_by_the_real_turn_runtime() -> None:
    """The value a runner will hand to `register_local_commitment`, unchanged."""
    import turn_builders

    turn = prepare(producer(), 1)
    live = turn_builders.runtime()
    live.cursor = turn.commitment.cursor
    live.register_local_commitment(turn.commitment)
    assert live.local_commitment is not None
    assert live.local_commitment.h_commit == turn.commitment.h_commit


def test_the_context_refuses_an_impossible_identity() -> None:
    """Our own identity is validated too - a bad one would poison every entry."""
    from mars777_police.app.outbound_evidence_values import LocalEvidenceContext

    with pytest.raises(ValueError, match="non-empty"):
        LocalEvidenceContext("", build.GAME_UID, 1, build.CONFIG, build.OURS)
    with pytest.raises(ValueError, match="positive int"):
        LocalEvidenceContext(build.GAME_ID, build.GAME_UID, 0, build.CONFIG, build.OURS)
