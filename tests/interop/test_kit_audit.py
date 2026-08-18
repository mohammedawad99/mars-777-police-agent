"""The external audit: two gates, and the honest gap between them.

A KIT peer's commitment chain can be perfectly verifiable while telling us
almost nothing about whether it played legally - the kit standardises
cryptographic correspondence, not payload meaning. So the audit asks two
separate questions and reports them separately.

**Gate 1** re-hashes the payload the peer revealed under the frozen codec. It
knows nothing about the game.

**Gate 2** weighs semantic evidence, and its vocabulary has four answers rather
than two. The pair that matters is `NOT_CHECKABLE` against `VERIFIED`: a peer
that sealed a leaner record has not proved it played legally, and recording
that as clean would score it as if it had. The other pair that matters is
`NOT_CHECKABLE` against `FAILED`: it also has not been caught doing anything,
and recording that as tampering would accuse an honest opponent.

Facts we already own are never asked of the peer. Role comes from the
authenticated session, the sub-game from the audit context, the configuration
from the verified lock, and the public barriers from the placements we
witnessed. A payload field may contradict those - which is a finding - but its
absence costs nothing.
"""

import pytest

from mars777_police.app.audit_status import CheckStatus
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.kit_audit import ExternalTurn, crypto_gate, semantic_checks
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.protocol.kit_commitment import kit_commitment

KIT = CommitmentCodec.KIT_CORE_COMMITMENT_V1
NONCE = "0f1e2d3c4b5a69788796a5b4c3d2e1f0"
CURSOR = TurnCursor(1, 4)


def sealed(**payload: object) -> ExternalTurn:
    body = dict(payload)
    return ExternalTurn(
        cursor=CURSOR,
        role=ActorRole.THIEF,
        payload=PeerPayload(body),
        nonce=NONCE,
        commit=kit_commitment(body, NONCE),
    )


# ------------------------------------------------------------------ gate 1


def test_a_faithful_payload_passes_the_crypto_gate() -> None:
    assert crypto_gate(sealed(step=4, move="MOVE:N"), KIT) is CheckStatus.VERIFIED


def test_a_rewritten_payload_fails_the_crypto_gate() -> None:
    turn = sealed(step=4, move="MOVE:N")
    tampered = ExternalTurn(
        cursor=turn.cursor,
        role=turn.role,
        payload=PeerPayload({"step": 4, "move": "MOVE:S"}),
        nonce=turn.nonce,
        commit=turn.commit,
    )

    assert crypto_gate(tampered, KIT) is CheckStatus.FAILED


def test_the_crypto_gate_says_nothing_about_legality() -> None:
    """An illegal move faithfully sealed still corresponds; that is gate 2's job."""
    assert crypto_gate(sealed(step=4, move="MOVE:NOWHERE"), KIT) is CheckStatus.VERIFIED


# ------------------------------------------------------------------ gate 2


def test_a_lean_lawful_payload_is_undecided_and_not_accused() -> None:
    """Four keys, none of them ours: nothing proved, nothing alleged."""
    outcomes = {one.name: one.status for one in semantic_checks(sealed(step=4), CURSOR)}

    assert outcomes["role"] is CheckStatus.VERIFIED
    assert outcomes["intent"] is CheckStatus.NOT_CHECKABLE
    assert CheckStatus.FAILED not in outcomes.values()


def test_a_contradicting_field_is_a_finding_rather_than_a_gap() -> None:
    """Evidence that disagrees with what we authoritatively know is a failure."""
    turn = sealed(step=4, role="police")
    outcomes = {one.name: one.status for one in semantic_checks(turn, CURSOR)}

    assert outcomes["role"] is CheckStatus.FAILED


def test_an_agreeing_field_is_verified() -> None:
    outcomes = {
        one.name: one.status for one in semantic_checks(sealed(step=4, role="thief"), CURSOR)
    }

    assert outcomes["role"] is CheckStatus.VERIFIED


def test_a_contradicting_step_is_a_finding() -> None:
    outcomes = {one.name: one.status for one in semantic_checks(sealed(step=9), CURSOR)}

    assert outcomes["step"] is CheckStatus.FAILED


def test_an_absent_step_costs_nothing_because_we_witnessed_it() -> None:
    """The cursor is ours; a peer need not seal it for us to know it."""
    outcomes = {one.name: one.status for one in semantic_checks(sealed(move="MOVE:N"), CURSOR)}

    assert outcomes["step"] is CheckStatus.VERIFIED


def test_a_contradicting_sub_game_is_a_finding() -> None:
    outcomes = {one.name: one.status for one in semantic_checks(sealed(sub_game=6), CURSOR)}

    assert outcomes["sub_game"] is CheckStatus.FAILED


@pytest.mark.parametrize("intent", ["truth", "lie"])
def test_a_lawful_intent_value_is_verified(intent: str) -> None:
    outcomes = {one.name: one.status for one in semantic_checks(sealed(intent=intent), CURSOR)}

    assert outcomes["intent"] is CheckStatus.VERIFIED


def test_an_intent_outside_the_vocabulary_is_a_finding() -> None:
    """C-08 fixes two words; a third is malformed, not a new classification."""
    outcomes = {one.name: one.status for one in semantic_checks(sealed(intent="maybe"), CURSOR)}

    assert outcomes["intent"] is CheckStatus.FAILED


def test_intent_is_never_derived_from_the_hint() -> None:
    """No NLP: a hint that reads like a lie proves nothing about the classification."""
    turn = sealed(hint="I am definitely not near the square")
    outcomes = {one.name: one.status for one in semantic_checks(turn, CURSOR)}

    assert outcomes["intent"] is CheckStatus.NOT_CHECKABLE


def test_every_check_carries_its_provenance() -> None:
    for outcome in semantic_checks(sealed(step=4), CURSOR):
        assert outcome.provenance is not None
