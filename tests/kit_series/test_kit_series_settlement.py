"""The message a series is only over once we have received, and the port that left.

A real six-sub-game series ended without a mutual settlement: both role backends
returned the moment their own last sub-game was disclosed and exited, the gateway
forwards `submit_audit` to the backend owning the live sub-game, that port was
gone, and the peer's `series_consensus` retries had nowhere to land. Appendix E
rule 35 scores a series with no agreed result **0 for both groups**.

These tests pin every hop of that path: the claim decodes, it is told apart from
a sub-game chain, it survives a round trip, whichever backend owns sub-game 6
waits for it, and a closed window is reported rather than absorbed.
"""

import asyncio

import pytest

from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim, KitRole
from mars777_police.app.kit_schedule import SUB_GAMES, schedule_for
from mars777_police.app.kit_settlement import plays_final_sub_game, settlement_within
from mars777_police.app.run_class import RunClassification
from mars777_police.infra.game_contract import consensus_window
from mars777_police.transport.codec_kit_pregame import decode_kit_audit, encode_kit_audit
from mars777_police.transport.kit_envelopes import KitAuditPayload, parse_kit

OBSERVED_SHA = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"
OBSERVED = {
    "sender": "police",
    "result_claim": "series_consensus",
    "records": [],
    "consensus_sha": OBSERVED_SHA,
}
"""The envelope a real peer actually sent, copied from the preserved receipt."""


def session() -> KitFriendlySession:
    return KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))


def settlement() -> KitAuditReveal:
    return KitAuditReveal(KitRole.POLICE, (), KitResultClaim.SERIES_CONSENSUS, OBSERVED_SHA)


def test_the_observed_settlement_envelope_parses() -> None:
    """The exact bytes a peer sent, which the outcome-only enum used to refuse."""
    reveal = decode_kit_audit(parse_kit(KitAuditPayload, OBSERVED))
    assert reveal.result_claim is KitResultClaim.SERIES_CONSENSUS
    assert reveal.consensus_sha == OBSERVED_SHA
    assert reveal.records == ()
    assert reveal.sender is KitRole.POLICE


def test_a_settlement_is_told_apart_from_a_sub_game_disclosure() -> None:
    assert settlement().settles_the_series
    assert not KitAuditReveal(KitRole.THIEF, (), KitResultClaim.SURVIVAL).settles_the_series


def test_the_settlement_survives_a_round_trip() -> None:
    assert encode_kit_audit(settlement()) == OBSERVED
    assert decode_kit_audit(parse_kit(KitAuditPayload, encode_kit_audit(settlement()))) == (
        settlement()
    )


def test_a_sub_game_disclosure_still_omits_the_digest_entirely() -> None:
    """Omission, never `null` - the same rule every optional member follows."""
    rendered = encode_kit_audit(KitAuditReveal(KitRole.THIEF, (), KitResultClaim.SURVIVAL))
    assert "consensus_sha" not in rendered


def test_a_settlement_never_lands_in_the_sub_game_slot() -> None:
    """The defect it would cause: re-hashed as a chain, refused for having none.

    A settlement carries no records. Judged as a sub-game disclosure it fails
    verification and is reported as the opponent's tamper - the opposite of what
    the message says.
    """
    live = session()
    live.deliver_audit(settlement())
    assert live.audit is None
    assert live.settlement == settlement()


def test_a_sub_game_disclosure_still_reaches_the_sub_game_slot() -> None:
    live = session()
    reveal = KitAuditReveal(KitRole.THIEF, (), KitResultClaim.SURVIVAL)
    live.deliver_audit(reveal)
    assert live.audit == reveal
    assert live.settlement is None


def test_a_settlement_arriving_early_is_not_discarded_by_the_next_sub_game() -> None:
    """It can land while the last sub-game is still draining its audit exchange."""
    live = session()
    live.deliver_audit(settlement())
    live.open_sub_game()
    assert live.settlement == settlement()


def test_the_waiting_side_is_whoever_owns_the_final_sub_game() -> None:
    police_first = schedule_for(KitRole.POLICE)
    ours = tuple(n for n, role in enumerate(police_first, start=1) if role is KitRole.POLICE)
    theirs = tuple(n for n, role in enumerate(police_first, start=1) if role is KitRole.THIEF)
    assert theirs[-1] == SUB_GAMES
    assert plays_final_sub_game(theirs)
    assert not plays_final_sub_game(ours)


def test_the_role_that_waits_flips_with_the_agreed_first_role() -> None:
    """Never hard-coded: sub-game 6 belongs to whichever role the schedule gives it."""
    for first in (KitRole.POLICE, KitRole.THIEF):
        rows = schedule_for(first)
        owner = rows[SUB_GAMES - 1]
        owned = tuple(n for n, role in enumerate(rows, start=1) if role is owner)
        assert plays_final_sub_game(owned)


def test_a_side_that_plays_nothing_waits_for_nothing() -> None:
    assert not plays_final_sub_game(())


def test_the_settlement_is_returned_when_it_arrives() -> None:
    live = session()

    async def run() -> KitAuditReveal | None:
        waiting = asyncio.create_task(settlement_within(live, 5.0))
        await asyncio.sleep(0)
        live.deliver_audit(settlement())
        return await waiting

    assert asyncio.run(run()) == settlement()


def test_a_closed_window_is_reported_rather_than_absorbed() -> None:
    """`None` is a fact about the series, not a settled series with no message."""
    assert asyncio.run(settlement_within(session(), 0.01)) is None


def test_the_window_comes_from_the_agreement_not_from_this_side() -> None:
    """The two sides finish at different moments; a local guess closes too early."""
    assert consensus_window() == 400.0


@pytest.mark.parametrize("claim", [one.value for one in KitResultClaim])
def test_every_claim_the_enum_names_is_accepted_on_the_wire(claim: str) -> None:
    """Wire and enum agree, so neither can gain a member the other refuses."""
    parsed = parse_kit(KitAuditPayload, {"sender": "thief", "records": [], "result_claim": claim})
    assert KitResultClaim(parsed.result_claim).value == claim
