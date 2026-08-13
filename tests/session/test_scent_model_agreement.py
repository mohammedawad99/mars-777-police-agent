"""Exact scent-model agreement, decided before `CONFIG_LOCKED` and nowhere else.

SCENT-003 asks the two sides to prove they interpret one model identically, so
the runtime reads the same question three ways - the values, the rendering each
side derives, and the digest each side derives - and requires all three. A peer's
own digest is never consulted, because a digest travelling beside the model it
covers proves nothing about it.

Malformed and disagreeing stay different things: a model our physics refuses is
stopped by the codec, and a model that is perfectly valid but simply not ours is
stopped here.
"""

import dataclasses

import pytest
import session_builders as build
from r16_builders import GROUP_A, GROUP_B, PROFILES, config
from session_builders import BUDGET, SUB_GAME, locker

from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.peer_pregame_messages import ConfigProposal
from mars777_police.app.protocol_errors import ConfigMismatchError
from mars777_police.app.scent_agreement import compare_models
from mars777_police.app.scent_model_identity import ScentModelRendering
from mars777_police.domain.scent_kernel import ScentKernel
from mars777_police.domain.scent_model import ScentModelAgreement
from mars777_police.domain.scent_model_default import FIGURE_4_WEIGHTS, default_scent_model
from mars777_police.protocol.config_lock import ConfigLockAuthenticator
from mars777_police.protocol.scent_model import scent_model_sha256

GOLDEN = "e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600"
CANONICAL_BYTES = 344


def alternate() -> ScentModelAgreement:
    """A valid, still-radial model that is simply not the one we agreed."""
    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        rows[row][col] = "0.03"
    return dataclasses.replace(default_scent_model(), kernel=ScentKernel.from_rows(rows))


def rebuilt() -> ScentModelAgreement:
    """An independently constructed model that is semantically the default."""
    return default_scent_model()


class SpyDigests:
    """The production adapter, plus a record of what the runtime asked it."""

    def __init__(self) -> None:
        self.inner = locker()
        self.renderings: list[ScentModelAgreement] = []
        self.digests: list[ScentModelAgreement] = []

    def digest(self, negotiated: object) -> object:
        """Delegate the config digest untouched."""
        return self.inner.digest(negotiated)  # type: ignore[arg-type]

    def scent_model_rendering(self, model: ScentModelAgreement) -> ScentModelRendering:
        """Record the ask, then answer exactly as production would."""
        self.renderings.append(model)
        return self.inner.scent_model_rendering(model)

    def scent_model_digest(self, model: ScentModelAgreement) -> object:
        """Record the ask, then answer exactly as production would."""
        self.digests.append(model)
        return self.inner.scent_model_digest(model)


def runtime(group_id: str, expected: ScentModelAgreement, digests: object = None) -> object:
    """A real negotiation runtime with an explicit local expectation."""
    return ConfigNegotiationRuntime(
        group_id, SUB_GAME, BUDGET, PROFILES, digests or locker(), expected
    )


def proposal_from(group_id: str, model: ScentModelAgreement | None) -> ConfigProposal:
    """What the peer sends us: a complete proposal carrying *model*."""
    return ConfigProposal(SUB_GAME, config(), PROFILES, model)


def test_the_adapter_renders_and_digests_the_default_model() -> None:
    adapter: ConfigLockAuthenticator = locker()
    model = default_scent_model()
    assert adapter.scent_model_rendering(model).length == CANONICAL_BYTES
    assert adapter.scent_model_digest(model).value == GOLDEN


def test_a_different_model_renders_and_digests_differently() -> None:
    adapter, other = locker(), alternate()
    assert adapter.scent_model_rendering(other) != adapter.scent_model_rendering(
        default_scent_model()
    )
    assert adapter.scent_model_digest(other).value != GOLDEN
    assert scent_model_sha256(other).value == adapter.scent_model_digest(other).value


def test_our_own_proposal_carries_the_model_we_expect() -> None:
    ours = runtime(GROUP_B, default_scent_model()).propose(config(), opening=True)
    assert ours.scent_model == default_scent_model()


def test_an_identical_model_rebuilt_independently_is_accepted() -> None:
    theirs = rebuilt()
    assert theirs is not default_scent_model(), "a distinct object, not an identity check"
    assert runtime(GROUP_A, default_scent_model()).accept(
        proposal_from(GROUP_B, theirs), GROUP_B, opening=True
    )


def test_a_valid_but_different_model_is_refused() -> None:
    with pytest.raises(ConfigMismatchError, match="not the one this side agreed"):
        runtime(GROUP_A, default_scent_model()).accept(
            proposal_from(GROUP_B, alternate()), GROUP_B, opening=True
        )


def test_a_missing_model_is_refused_as_a_config_mismatch() -> None:
    """`None` is structurally legal in the codec and unacceptable here."""
    with pytest.raises(ConfigMismatchError, match="required pre-game term and is absent"):
        runtime(GROUP_A, default_scent_model()).accept(
            proposal_from(GROUP_B, None), GROUP_B, opening=True
        )


def test_the_refusal_carries_the_existing_config_mismatch_identity() -> None:
    with pytest.raises(ConfigMismatchError) as failure:
        runtime(GROUP_A, default_scent_model()).accept(
            proposal_from(GROUP_B, alternate()), GROUP_B, opening=True
        )
    assert failure.value.error_id == "E-CONFIG-MISMATCH"


def test_all_three_readings_are_taken_for_an_accepted_model() -> None:
    spy = SpyDigests()
    runtime(GROUP_A, default_scent_model(), spy).accept(
        proposal_from(GROUP_B, rebuilt()), GROUP_B, opening=True
    )
    assert len(spy.renderings) == 2, "ours and theirs"
    assert len(spy.digests) == 2, "ours and theirs"


def test_all_three_readings_are_taken_before_a_refusal() -> None:
    """No short circuit: a mismatch still exercises every comparison."""
    spy = SpyDigests()
    with pytest.raises(ConfigMismatchError):
        runtime(GROUP_A, default_scent_model(), spy).accept(
            proposal_from(GROUP_B, alternate()), GROUP_B, opening=True
        )
    assert len(spy.renderings) == 2
    assert len(spy.digests) == 2


def test_the_comparison_reports_each_reading_separately() -> None:
    ours, adapter = default_scent_model(), locker()
    same = compare_models(ours, rebuilt(), adapter)
    assert (same.same_values, same.same_rendering, same.same_digest) == (True, True, True)
    assert same.agreed
    different = compare_models(ours, alternate(), adapter)
    assert (different.same_values, different.same_rendering, different.same_digest) == (
        False,
        False,
        False,
    )
    assert not different.agreed


def test_a_rendering_is_a_semantic_value_not_a_byte_string() -> None:
    with pytest.raises(ValueError, match="non-empty encoded content"):
        ScentModelRendering(b"")
    with pytest.raises(ValueError, match="non-empty encoded content"):
        ScentModelRendering("0.9")  # type: ignore[arg-type]


def test_the_model_check_runs_after_the_existing_config_and_profile_checks() -> None:
    """An already-invalid config keeps its own identity, unmasked by the model."""
    lowered = dataclasses.replace(
        config(),
        network_and_league=dataclasses.replace(
            config().network_and_league, token_budget_per_series=150000
        ),
    )
    proposal = ConfigProposal(SUB_GAME, lowered, PROFILES, alternate())
    with pytest.raises(ConfigMismatchError, match="token_budget_per_series"):
        runtime(GROUP_A, default_scent_model()).accept(proposal, GROUP_B, opening=True)


def test_a_refused_model_leaves_the_pregame_round_unlocked() -> None:
    pregame = build.pregame()
    with pytest.raises(ConfigMismatchError):
        pregame.accept_proposal(proposal_from(GROUP_B, alternate()), GROUP_B)
    assert pregame.config is None, "no config was adopted, so no lock can follow"
