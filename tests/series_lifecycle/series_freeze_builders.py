"""Two real composed agents driving real config rounds, one model at a time.

Nothing here fakes a lock. The rounds are built from each side's own production
adapters, the proposal is the one `ConfigNegotiationRuntime` produces, and the
evidence each side accepts is the other's real keyed proof - so a refusal seen
by a test using these builders came from production code.
"""

import dataclasses
from pathlib import Path

import boot_builders as boot
import r7_builders as r7
from r16_builders import GAME_ID, GAME_UID, GROUP_A, GROUP_B, PROFILES
from session_builders import BUDGET

from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.scent_kernel import ScentKernel
from mars777_police.domain.scent_model import ScentModelAgreement
from mars777_police.domain.scent_model_default import FIGURE_4_WEIGHTS, default_scent_model
from mars777_police.series_runtime import SeriesRuntime

GOLDEN = Sha256Digest("e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600")
SUB_GAMES = (1, 2, 3, 4, 5, 6)
"""The six sub-games a series plays; `num_games` is not reopened here."""


def model_b() -> ScentModelAgreement:
    """A second valid, still-radial model - the one nobody may switch to."""
    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        rows[row][col] = "0.03"
    return dataclasses.replace(default_scent_model(), kernel=ScentKernel.from_rows(rows))


def pair(root: Path) -> tuple[SeriesRuntime, SeriesRuntime]:
    """Two real composed agents and their series owners, each with its own root."""
    agent_a, agent_b = r7.agents(*boot.pair_urls())
    return (
        r7.series_for(agent_a, r7.store_for(root / "police")),
        r7.series_for(agent_b, r7.store_for(root / "thief")),
    )


def open_round(
    series: SeriesRuntime, group_id: str, sub_game: int, model: ScentModelAgreement
) -> None:
    """Open one real config round on this side's own pregame owner."""
    pregame = series.composition.pregame
    digests, auth = pregame.lock.digester, pregame.lock.auth
    pregame.open_round(
        ConfigNegotiationRuntime(group_id, sub_game, BUDGET, PROFILES, digests, model),
        ConfigLockRuntime(GAME_ID, GAME_UID, sub_game, PROFILES, digests, auth, model),
    )


def negotiate(
    a: SeriesRuntime, b: SeriesRuntime, sub_game: int, model: ScentModelAgreement
) -> None:
    """Both sides really propose, agree and adopt this sub-game's config."""
    open_round(a, GROUP_A, sub_game, model)
    open_round(b, GROUP_B, sub_game, model)
    proposal = b.composition.pregame.prepare_proposal(r7.CONFIG)
    assert a.composition.pregame.accept_proposal(proposal, GROUP_B) is True
    for series in (a, b):
        series.composition.pregame.adopt_config(r7.CONFIG)


def lock(
    a: SeriesRuntime, b: SeriesRuntime, sub_game: int, model: ScentModelAgreement | None = None
) -> None:
    """One whole real config round: negotiate, exchange evidence, verify both."""
    negotiate(a, b, sub_game, model or default_scent_model())
    a.composition.pregame.accept_lock(b.composition.pregame.prepare_lock())
    b.composition.pregame.accept_lock(a.composition.pregame.prepare_lock())


def frozen(series: SeriesRuntime) -> Sha256Digest | None:
    """What this side's series is committed to, if anything yet."""
    return series.composition.pregame.scent_freeze.identity
