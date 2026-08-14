"""The series' scent-model identity as a value, and where the session keeps it.

`SeriesScentFreeze` answers one question - what model is this series committed
to - and answers it immutably: establishing returns a freeze rather than
changing one, so the only way a later sub-game could overwrite `g01`'s decision
would be for somebody to build a different value and store it deliberately.

The lifecycle proof lives beside the real two-agent series; what is checked here
is the value's own arithmetic and the one place the pregame session applies it.
"""

import dataclasses

import pytest
import session_builders as build
from session_builders import locker

from mars777_police.app.pregame_session_runtime import PregameSessionRuntime
from mars777_police.app.protocol_errors import (
    ConfigMismatchError,
    LocalDefectError,
    StaleMessageError,
)
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.series_scent_freeze import SeriesScentFreeze
from mars777_police.domain.scent_model_default import default_scent_model

GOLDEN = Sha256Digest("e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600")
OTHER = Sha256Digest("b" * 64)


def locked() -> PregameSessionRuntime:
    """A pregame session that has verified one lock, exactly as production does."""
    runtime = build.pregame()
    runtime.adopt_config(build.agreed())
    runtime.accept_lock(build.lock_evidence_for(1))
    return runtime


def test_a_fresh_freeze_is_committed_to_nothing() -> None:
    assert SeriesScentFreeze().identity is None
    assert SeriesScentFreeze() == SeriesScentFreeze()


def test_establishing_returns_a_freeze_and_never_mutates_one() -> None:
    empty = SeriesScentFreeze()
    established = empty.established(GOLDEN)
    assert empty.identity is None, "the value it was called on is untouched"
    assert established.identity == GOLDEN


def test_the_same_identity_is_idempotent_however_often_it_is_relocked() -> None:
    """Six sub-games locking one model is six calls, not six transitions."""
    freeze = SeriesScentFreeze().established(GOLDEN)
    for _ in range(5):
        freeze = freeze.established(GOLDEN)
    assert freeze.identity == GOLDEN


def test_a_different_identity_is_refused_as_a_config_mismatch() -> None:
    freeze = SeriesScentFreeze().established(GOLDEN)
    with pytest.raises(ConfigMismatchError, match="already locked its scent model") as refusal:
        freeze.established(OTHER)
    assert refusal.value.error_id == "E-CONFIG-MISMATCH"
    assert freeze.identity == GOLDEN, "the refusal changed nothing"


def test_the_refusal_says_that_agreeing_together_is_not_enough() -> None:
    with pytest.raises(ConfigMismatchError, match="however validly both sides agreed"):
        SeriesScentFreeze(GOLDEN).established(OTHER)


def test_a_frozen_identity_cannot_be_assigned_over() -> None:
    freeze = SeriesScentFreeze(GOLDEN)
    with pytest.raises(dataclasses.FrozenInstanceError):
        freeze.identity = OTHER  # type: ignore[misc]


def test_only_a_real_digest_may_be_frozen() -> None:
    with pytest.raises(LocalDefectError, match="must be a Sha256Digest"):
        SeriesScentFreeze("e" * 64)  # type: ignore[arg-type]


def test_the_freeze_holds_the_identity_alone() -> None:
    """No kernel copy, no model, no proof - the digest is the whole record."""
    members = {field.name for field in dataclasses.fields(SeriesScentFreeze)}
    assert members == {"identity"}


def test_a_pregame_session_starts_with_no_series_model() -> None:
    assert build.pregame().scent_freeze.identity is None


def test_a_verified_lock_freezes_the_model_the_session_agreed() -> None:
    runtime = locked()
    assert runtime.scent_freeze.identity == GOLDEN
    assert runtime.scent_freeze.identity == locker().scent_model_digest(default_scent_model())


def test_a_repeated_lock_of_the_same_round_stays_on_the_same_model() -> None:
    """Retrying one sub-game's lock is not a second decision."""
    runtime = locked()
    runtime.accept_lock(build.lock_evidence_for(1))
    assert runtime.scent_freeze.identity == GOLDEN


def test_opening_the_next_round_keeps_the_series_model() -> None:
    """`open_round` resets what belongs to a sub-game; this belongs to the series."""
    runtime = locked()
    runtime.open_round(*build.round_of(2))
    assert runtime.config is None, "the round itself did reset"
    assert runtime.scent_freeze.identity == GOLDEN


def test_a_later_round_locking_the_same_model_is_accepted() -> None:
    runtime = locked()
    runtime.open_round(*build.round_of(2))
    runtime.adopt_config(build.agreed())
    runtime.accept_lock(build.lock_evidence_for(2))
    assert runtime.scent_freeze.identity == GOLDEN


def test_a_lock_that_fails_earlier_never_reaches_the_series_freeze() -> None:
    """The digest is taken from a verified lock, so a stale one changes nothing."""
    runtime = build.pregame()
    runtime.adopt_config(build.agreed())
    with pytest.raises(StaleMessageError, match="sub-game"):
        runtime.accept_lock(build.lock_evidence_for(2))
    assert runtime.scent_freeze.identity is None
