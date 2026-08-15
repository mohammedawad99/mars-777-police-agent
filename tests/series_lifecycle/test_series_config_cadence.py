"""The order a config round has to happen in, and the defect that ignored it.

`PregameSessionRuntime.accept_lock` refuses evidence that arrives before this
side agreed a config - correctly, because a lock verifies *our* digest of *our*
config and there is nothing to compare against otherwise. The first
`SeriesDriver` adopted its config only just before sending its own lock, which
left a window in which our lock reached a peer that had opened its round but not
yet adopted. Both sides then raised `E-PROTO-STALE` at each other and `g01`
never got past negotiation.

The fix is sequencing, not tolerance: a round adopts the config it was opened
for at the moment it opens, so anything the peer sends afterwards has something
to verify against. These tests pin that, and they use the production
`SeriesDriver.open()` path rather than hand-built state.
"""

import asyncio
from pathlib import Path

import autonomous_series_builders as auto
import pytest

from mars777_police.app.config_negotiation_runtime import initial_proposer
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_agreements import agree_config


@pytest.fixture
def opened(tmp_path: Path) -> tuple[object, object]:
    """Two real agents whose series drivers have opened `g01` and nothing more."""
    a, b = auto.pair_for(tmp_path)
    drivers = (auto.driver_for(a, ActorRole.POLICE), auto.driver_for(b, ActorRole.THIEF))
    for driver in drivers:
        driver.open()
    return a, b


def test_opening_a_round_leaves_it_able_to_verify_an_incoming_lock(opened: tuple) -> None:
    """The defect: an opened round with no config refuses the peer's lock."""
    for series in opened:
        assert series.composition.pregame.config is not None


def test_a_lock_arriving_first_is_still_verifiable_after_open(opened: tuple) -> None:
    a, b = opened
    evidence = a.composition.pregame.prepare_lock()
    b.composition.pregame.accept_lock(evidence)
    assert b.composition.pregame.locked_evidence is not None
    assert b.composition.pregame.milestones.lock_verified.is_set()


def test_a_round_that_was_never_opened_still_refuses_a_lock(opened: tuple) -> None:
    """The guard itself is untouched: no config, no verification."""
    from mars777_police.app.pregame_rounds import open_next_round

    a, b = opened
    evidence = a.composition.pregame.prepare_lock()
    b.composition.pregame.open_round(b.composition.pregame.negotiation, b.composition.pregame.lock)
    assert b.composition.pregame.config is None
    with pytest.raises(StaleMessageError, match="before this side agreed a config"):
        b.composition.pregame.accept_lock(evidence)
    open_next_round(b.composition.pregame, 1)


def test_opening_the_next_round_readopts_before_anything_can_arrive(opened: tuple) -> None:
    a, _ = opened
    driver = auto.driver_for(a, ActorRole.POLICE)
    driver.open()
    assert a.composition.pregame.config is not None
    assert a.composition.pregame.negotiation.sub_game == a.sub_game


def test_the_real_g01_config_round_completes_through_production_owners(
    tmp_path: Path,
) -> None:
    """Proposal, adoption and lock for `g01`, driven only by the series owner."""
    a, b = auto.pair_for(tmp_path)
    drivers = (auto.driver_for(a, ActorRole.POLICE), auto.driver_for(b, ActorRole.THIEF))

    async def run() -> None:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            await asyncio.gather(
                *(
                    agree_config(
                        series.composition.pregame,
                        series.composition.peer_runner,
                        auto.r7.CONFIG,
                        driver._await,
                    )
                    for series, driver in zip((a, b), drivers, strict=True)
                )
            )

    asyncio.run(run())
    opener = initial_proposer(auto.r7.CONFIG)
    ids = [series.composition.pregame.negotiation.group_id for series in (a, b)]
    assert opener in ids
    assert opener == min(ids)
    digests = [
        series.composition.pregame.lock.digester.digest(series.composition.pregame.config)
        for series in (a, b)
    ]
    assert digests[0] == digests[1]
    for series in (a, b):
        pregame = series.composition.pregame
        assert pregame.locked_evidence is not None
        assert pregame.milestones.proposal_seen.is_set()
        assert pregame.milestones.lock_verified.is_set()
        assert pregame.scent_freeze.identity is not None
        series.lock_config(pregame.config)
    for side in ("police", "thief"):
        stored = sorted(path.name for path in (tmp_path / side).iterdir())
        assert [one for one in stored if one.startswith("config_")] != []
