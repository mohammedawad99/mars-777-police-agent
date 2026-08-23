"""One real emission, sent once, and the only story about it the audit accepts.

Nothing is hand-built. Two production sides negotiate over real FastMCP, one of
them seals a turn and reveals it with the emission production projected from the
same action, the other retains exactly what arrived, and then the sender renders
its ordinary disclosure from retained history and sends that too. The emission
that crosses live and the emission in the document are asserted to be the same
object's value, not two equal-looking fixtures.

The second half is the same run with one member rewritten. The forged document is
*structurally perfect* - it parses, its entries still hash, its capture transcript
still matches - and it is refused anyway, because the scent it discloses is not
the scent that arrived. That is the property this checkpoint exists to establish:
history that has been observed cannot be re-authored at disclosure time.
"""

import asyncio
from collections.abc import Iterator

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A, GROUP_B
from test_runner_two_sided import CURSOR, sealed, step0_on

from mars777_police.app.audit_disclosure_writer import scent_value
from mars777_police.app.capture_transcript import TranscriptMismatchError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.board import Position
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    """Side A and side B, each behind its own real inbound server."""
    a = build.side(GROUP_A, ActorRole.POLICE)
    b = build.side(GROUP_B, ActorRole.THIEF)
    with build.server_for(a) as server_a, build.server_for(b) as server_b:
        a.url, b.url = server_a.url, server_b.url
        yield a, b


async def one_disclosed_turn(a: object, b: object) -> tuple[object, object]:
    """Step-0, commit, ack, reveal, nonces - and stop before the disclosure."""
    a_to_b = await step0_on(a, b.url)
    b_to_a = await step0_on(b, a.url)
    prepared = await a.runner(a_to_b).open_turn(
        state=sealed(ActorRole.POLICE),
        action=turn_builders.legal_reveal().action,
        intent=Intent.TRUTH,
        hint="heading north",
        cursor=CURSOR,
    )
    await b.runner(b_to_a).acknowledge_peer_turn()
    await a.runner(a_to_b).reveal_turn(prepared)
    b.audit = build.audit_over(b.turn, a.group_id, ActorRole.POLICE)
    await a.runner(a_to_b).send_final_nonce_reveal()
    return prepared, a_to_b


def test_the_emission_that_was_sent_is_the_emission_that_is_disclosed(pair: tuple) -> None:
    """Live, retained and disclosed are one value carried through, not three."""
    a, b = pair
    prepared = asyncio.run(_honest(a, b))

    sent = prepared.reveal.scent_emission
    assert sent is not None
    (retained,) = a.turn.capture.sent_scent
    assert retained == ScentRecord(CURSOR, sent), "the sender kept exactly what it sent"
    (witnessed,) = b.audit.expected_scent
    assert witnessed.emission == sent, "the receiver kept exactly what arrived"
    (disclosed,) = b.audit.disclosure["scent"]
    assert disclosed == scent_value(ScentRecord(CURSOR, sent))
    assert b.audit.verdict is FinalAuditVerdict.VERIFIED_OK


def test_the_disclosure_is_rendered_from_history_and_not_reprojected(pair: tuple) -> None:
    """The sender's own evidence owner holds the row the reveal already carried."""
    a, b = pair
    prepared = asyncio.run(_honest(a, b))
    assert a.producer.scent == a.turn.capture.sent_scent
    assert a.producer.scent == (ScentRecord(CURSOR, prepared.reveal.scent_emission),)


def test_a_rewritten_emission_is_refused_though_the_document_is_perfect(pair: tuple) -> None:
    """Structurally valid, cryptographically intact, and not what arrived."""
    a, b = pair
    forged, honest = asyncio.run(_forged(a, b))

    assert forged["scent"] != honest["scent"], "exactly one member was rewritten"
    assert forged["entries"] == honest["entries"], "the sealed entries are untouched"
    assert forged["capture"] == honest["capture"], "the capture transcript is untouched"
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        b.audit.accept_audit_disclosure(forged)
    assert b.audit.verdict is None, "no verdict is reached on a contradicted history"


def test_the_same_run_verifies_when_the_scent_is_left_alone(pair: tuple) -> None:
    """The control: only the rewrite is what fails, not the harness."""
    a, b = pair
    _, honest = asyncio.run(_forged(a, b))
    b.audit.accept_audit_disclosure(honest)
    assert b.audit.verdict is FinalAuditVerdict.VERIFIED_OK


async def _honest(a: object, b: object) -> object:
    """A whole honest turn, disclosure included, over the one live session."""
    prepared, a_to_b = await one_disclosed_turn(a, b)
    await a.runner(a_to_b).send_audit_disclosure()
    return prepared


async def _forged(a: object, b: object) -> tuple[dict, dict]:
    """The real document, and a copy with only its scent member re-authored."""
    await one_disclosed_turn(a, b)
    honest = a.producer.audit_disclosure()
    model = default_scent_model()
    elsewhere = emission_of(turn_builders.board(), model.kernel, Position(2, 2), model.params)
    row = ScentRecord(TurnCursor(CURSOR.sub_game, CURSOR.step), elsewhere)
    return {**honest, "scent": [scent_value(row)]}, honest
