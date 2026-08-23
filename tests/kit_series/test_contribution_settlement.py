"""What a contribution says about the settlement, including when there was none.

A series that reached its last sub-game and a series that was *mutually settled*
are different facts, and rule 35 scores the difference. The evidence has to be
able to tell them apart, so the digest is written when one arrived and the key is
absent when none did - never a `null` that reads as "settled with nothing".
"""

from mars777_police.app.friendly_merge import contribution_document
from mars777_police.app.kit_messages import KitRole

SHA = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"


def document(consensus: str | None) -> dict[str, object]:
    return dict(
        contribution_document(
            role=KitRole.THIEF,
            game_id="MaRs-777-vs-s82kma9e",
            game_uid="uid0001",
            our_group="MaRs-777",
            peer_group="s82kma9e",
            rows=(),
            series_consensus_sha256=consensus,
        )
    )


def test_a_settled_series_records_the_digest_it_settled_on() -> None:
    assert document(SHA)["series_consensus_sha256"] == SHA


def test_an_unsettled_series_omits_the_key_rather_than_nulling_it() -> None:
    """Absent, so a reader cannot mistake "no settlement" for "settled on null"."""
    assert "series_consensus_sha256" not in document(None)


def test_the_settlement_never_displaces_a_contribution_member() -> None:
    settled, unsettled = document(SHA), document(None)
    assert set(unsettled) < set(settled)
    assert set(settled) - set(unsettled) == {"series_consensus_sha256"}
    for name in ("evidence_class", "role", "game_id", "game_uid", "group_id"):
        assert settled[name] == unsettled[name]
