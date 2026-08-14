"""One agreed scent model, frozen for a whole six-sub-game series.

Two really composed agents, their production `PregameSessionRuntime`s and the
real keyed lock: `g01` establishes the identity by locking it, and every later
sub-game has to bring the same one back.

The test that matters most is the both-peers switch. Every per-sub-game layer
below approves it - the codec parses the new model, strict agreement finds the
two sides equal, and the lock proof verifies over its digest - and the series
still refuses it, because "we both changed our minds after g01" is exactly what
a series-wide agreement is supposed to make impossible.
"""

import dataclasses
from pathlib import Path

import pytest
import r7_builders as r7
from r16_builders import GROUP_A, GROUP_B
from series_freeze_builders import (
    GOLDEN,
    SUB_GAMES,
    frozen,
    lock,
    model_b,
    negotiate,
    open_round,
    pair,
)

from mars777_police.app.protocol_errors import ConfigMismatchError, StaleMessageError
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.scent_model import scent_model_sha256


def test_a_fresh_series_has_frozen_no_scent_model(tmp_path: Path) -> None:
    a, b = pair(tmp_path)
    assert frozen(a) is None and frozen(b) is None


def test_the_first_sub_game_freezes_the_model_it_locked(tmp_path: Path) -> None:
    a, b = pair(tmp_path)
    lock(a, b, 1)
    assert frozen(a) == frozen(b) == GOLDEN == scent_model_sha256(default_scent_model())


def test_the_freeze_happens_before_any_gameplay_of_the_first_sub_game(tmp_path: Path) -> None:
    """Locked and frozen, with no turn, no outcome line and no log on disk."""
    a, b = pair(tmp_path)
    lock(a, b, 1)
    for series in (a, b):
        assert frozen(series) == GOLDEN
        assert series.lines == ()
        with pytest.raises(StaleMessageError, match="no turn is active"):
            series.composition.runtime_context.current_turn()
    assert list(tmp_path.glob("*/log_*.json")) == []


def test_the_same_model_is_relocked_by_every_one_of_the_six_sub_games(tmp_path: Path) -> None:
    a, b = pair(tmp_path)
    for sub_game in SUB_GAMES:
        lock(a, b, sub_game)
        assert frozen(a) == frozen(b) == GOLDEN, f"g0{sub_game} moved the series' model"
    assert a.composition.pregame.lock.sub_game == SUB_GAMES[-1]


def test_both_peers_switching_together_is_still_refused_by_the_series(tmp_path: Path) -> None:
    """The whole point: every per-sub-game layer approves, the series does not."""
    a, b = pair(tmp_path)
    lock(a, b, 1)
    negotiate(a, b, 2, model_b())
    evidence = b.composition.pregame.prepare_lock()
    pregame = a.composition.pregame
    pregame.lock.accept(evidence, pregame.lock.digester.digest(r7.CONFIG))
    assert pregame.lock.auth.verify(evidence.context, evidence.auth)
    with pytest.raises(ConfigMismatchError, match="already locked its scent model") as refusal:
        pregame.accept_lock(evidence)
    assert refusal.value.error_id == "E-CONFIG-MISMATCH"


def test_a_refused_switch_leaves_the_frozen_identity_and_no_gameplay(tmp_path: Path) -> None:
    a, b = pair(tmp_path)
    lock(a, b, 1)
    negotiate(a, b, 2, model_b())
    with pytest.raises(ConfigMismatchError):
        a.composition.pregame.accept_lock(b.composition.pregame.prepare_lock())
    assert frozen(a) == GOLDEN
    assert a.lines == () and list(tmp_path.glob("*/log_*.json")) == []
    lock(a, b, 2)
    assert frozen(a) == GOLDEN, "the retry on the agreed model is what recovers"


def test_one_peer_switching_still_fails_at_the_agreement_layer(tmp_path: Path) -> None:
    """The series freeze adds a layer; it never takes the earlier refusal over."""
    a, b = pair(tmp_path)
    lock(a, b, 1)
    open_round(a, GROUP_A, 2, default_scent_model())
    open_round(b, GROUP_B, 2, model_b())
    proposal = b.composition.pregame.prepare_proposal(r7.CONFIG)
    with pytest.raises(ConfigMismatchError, match="not the one this side agreed"):
        a.composition.pregame.accept_proposal(proposal, GROUP_B)
    assert frozen(a) == GOLDEN


def test_a_separate_series_may_freeze_a_different_model(tmp_path: Path) -> None:
    """Series-level, not process-global: nothing leaks from the first pair."""
    first, second = pair(tmp_path / "one"), pair(tmp_path / "two")
    lock(*first, 1)
    assert frozen(second[0]) is None
    lock(*second, 1, model_b())
    assert frozen(second[0]) == frozen(second[1]) == scent_model_sha256(model_b())
    assert frozen(first[0]) == GOLDEN


def test_the_series_cursor_still_owns_which_sub_game_comes_first(tmp_path: Path) -> None:
    """The freeze neither moves nor duplicates the orchestrator's cursor."""
    a, b = pair(tmp_path)
    assert a.sub_game == 1
    lock(a, b, 1)
    assert a.sub_game == 1 and b.sub_game == 1
    members = {field.name for field in dataclasses.fields(a.composition.pregame.scent_freeze)}
    assert members == {"identity"}, "no second cursor, and no sub-game rule of its own"
