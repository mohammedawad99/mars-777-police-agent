"""Two peers that boot with different legal configs must not both lock one.

`SeriesDriver.open()` adopts the config this side was booted with, which is what
lets an arriving lock be verified at all. The obvious worry is that adopting
early turns negotiation into a ceremony - each side rubber-stamping its own
input and locking regardless. It does not, and this is where that is proved.

The enforcement point is **not** the proposal. `ConfigNegotiationRuntime.accept`
validates a proposal's terms, profiles and scent model and then returns `True`;
it never compares the peer's config with ours, and `converges` has no caller.
Agreement is decided one step later, by `ConfigLockRuntime.accept`, which
recomputes *our* digest of *our* config and refuses evidence that names a
different one - `ConfigMismatchError`, the frozen `E-CONFIG-MISMATCH` identity.

The mismatch below uses `hint_max_words`, which App F T14 #2 marks NEGOTIABLE,
so both sides hold a fully legal config and no FIXED value is bent to
manufacture the disagreement.
"""

import asyncio
import dataclasses
from pathlib import Path

import autonomous_series_builders as auto
import pytest
import r7_builders as r7

from mars777_police.app.protocol_errors import ConfigMismatchError
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_agreements import agree_config
from mars777_police.domain.config_sections import WorldTerms

OTHER = dataclasses.replace(
    r7.CONFIG, world=WorldTerms(map_area=r7.CONFIG.world.map_area, hint_max_words=12)
)
"""The same series, booted with a different but entirely legal word budget."""


def test_the_mismatched_input_is_itself_a_legal_config() -> None:
    assert OTHER != r7.CONFIG
    assert OTHER.world.hint_max_words == 12
    assert OTHER.movement_and_barriers == r7.CONFIG.movement_and_barriers
    assert OTHER.board_and_agents == r7.CONFIG.board_and_agents


def _disagreeing(root: Path) -> tuple[object, object, tuple[object, object]]:
    a, b = auto.pair_for(root)
    police = auto.driver_for(a, ActorRole.POLICE)
    thief = dataclasses.replace(auto.driver_for(b, ActorRole.THIEF), config=OTHER)
    return a, b, (police, thief)


def test_disagreeing_peers_never_both_reach_a_verified_lock(tmp_path: Path) -> None:
    a, b, drivers = _disagreeing(tmp_path)

    async def run() -> None:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            await asyncio.gather(
                *(
                    agree_config(
                        series.composition.pregame,
                        series.composition.peer_runner,
                        driver.config,
                        driver._await,
                    )
                    for series, driver in zip((a, b), drivers, strict=True)
                )
            )

    with pytest.raises(ConfigMismatchError):
        asyncio.run(run())
    assert [series.composition.pregame.locked_evidence for series in (a, b)].count(None) >= 1


def test_a_disagreement_writes_no_config_artifact(tmp_path: Path) -> None:
    a, b, drivers = _disagreeing(tmp_path)

    async def run() -> None:
        async with auto.started(a, b):
            for driver in drivers:
                driver.open()
            await asyncio.gather(
                *(
                    agree_config(
                        series.composition.pregame,
                        series.composition.peer_runner,
                        driver.config,
                        driver._await,
                    )
                    for series, driver in zip((a, b), drivers, strict=True)
                )
            )

    with pytest.raises(ConfigMismatchError):
        asyncio.run(run())
    for side in ("police", "thief"):
        written = list((tmp_path / side).iterdir()) if (tmp_path / side).exists() else []
        assert [path for path in written if path.name.startswith("config_")] == []


def test_the_lock_is_what_refuses_it_not_the_proposal() -> None:
    """A differing proposal is accepted; the digest comparison is the authority."""
    import runner_builders as build
    from r16_builders import GROUP_A, GROUP_B

    opener = build.side(GROUP_B, "group_b", ActorRole.THIEF)
    receiver = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    proposal = opener.pregame.negotiation.propose(OTHER, opening=True)
    assert receiver.pregame.negotiation.accept(proposal, GROUP_B, opening=True) is True


def test_convergence_is_never_decided_by_the_proposal_exchange() -> None:
    """`accept` reports validity, not agreement - `converges` has no caller."""
    from pathlib import Path as _Path

    callers = [
        path
        for path in _Path("src/mars777_police").rglob("*.py")
        if ".converges(" in path.read_text(encoding="utf-8")
    ]
    assert callers == []
