"""A peer that speaks a different turn contract is refused before the lock.

The response shape is not discoverable from a request, so it is settled while a
config can still be refused - never by sniffing the first reveal, and never by
falling back from `TurnOutcome` to a legality `bool`.
"""

import dataclasses

import pytest
import session_builders as build
from r16_builders import GROUP_B, PROFILES, config

from mars777_police.app.interop_profiles import COUNTED_TURN_PROFILE, CompatibilityProfile
from mars777_police.app.peer_pregame_messages import ConfigProposal
from mars777_police.app.protocol_errors import ConfigMismatchError
from mars777_police.app.state_machine import ProtocolPhase
from mars777_police.app.turn_contract_gate import require_counted_turn_contract
from mars777_police.domain.scent_model_default import default_scent_model

LEGACY = CompatibilityProfile.STRICT_COUNTED_MATCH
LEGACY_V1 = CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_V1
CURRENT = CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2


def posture(profile: CompatibilityProfile) -> object:
    """The frozen profile set with one posture swapped."""
    return dataclasses.replace(PROFILES, compatibility_profile=profile)


def test_the_current_counted_posture_passes_the_gate() -> None:
    assert PROFILES.compatibility_profile is CURRENT
    assert CURRENT.value == COUNTED_TURN_PROFILE
    require_counted_turn_contract(PROFILES)


@pytest.mark.parametrize(
    "profile",
    [
        LEGACY,
        LEGACY_V1,
        CompatibilityProfile.LECTURER_REFERENCE_COMPATIBILITY,
        CompatibilityProfile.LECTURER_ATTACHMENT_COMPATIBILITY,
    ],
)
def test_every_other_posture_is_refused(profile: CompatibilityProfile) -> None:
    """Including the legacy bool posture, which keeps its old meaning."""
    with pytest.raises(ConfigMismatchError, match=COUNTED_TURN_PROFILE):
        require_counted_turn_contract(posture(profile))


def test_a_legacy_peer_is_refused_while_the_config_can_still_be_refused() -> None:
    """The refusal lands on the peer's proposal, long before `CONFIG_LOCKED`."""
    pregame = build.pregame()
    proposal = ConfigProposal(1, config(), posture(LEGACY), default_scent_model())
    with pytest.raises(ConfigMismatchError, match="different turn contract"):
        pregame.accept_proposal(proposal, GROUP_B)
    assert pregame.config is None
    assert ProtocolPhase.CONFIG_LOCKED.value == "CONFIG_LOCKED"


def test_the_refusal_leaves_no_round_state_behind() -> None:
    pregame = build.pregame()
    before = (pregame.opening, pregame.seen, pregame.config)
    with pytest.raises(ConfigMismatchError):
        pregame.accept_proposal(
            ConfigProposal(1, config(), posture(LEGACY), default_scent_model()), GROUP_B
        )
    assert (pregame.opening, pregame.seen, pregame.config) == before


def test_the_matching_current_posture_is_accepted_by_the_real_runtime() -> None:
    pregame = build.pregame()
    assert (
        pregame.accept_proposal(
            ConfigProposal(1, config(), PROFILES, default_scent_model()), GROUP_B
        )
        is True
    )
    assert pregame.seen == frozenset({GROUP_B})
