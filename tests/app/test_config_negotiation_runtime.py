"""Config negotiation: the deterministic proposer, and the bounded cadence.

The pinned case is the one that matters: `GROUP-XY` is byte-wise lower than
`MaRs-777` *and* occupies the `group_b` slot, so a rule keyed on the slot would
pick the wrong opener in a real match.
"""

from dataclasses import replace

import pytest
from r16_builders import GROUP_A, GROUP_B, PROFILES, config

from mars777_police.app.auth_values import AuthProfile, KeyId
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime, initial_proposer
from mars777_police.app.interop_profiles import SeriesConvention
from mars777_police.app.protocol_errors import (
    ConfigMismatchError,
    ConventionMismatchError,
    LocalDefectError,
    StaleMessageError,
)
from mars777_police.domain.config_league_sections import NetworkAndLeagueTerms
from mars777_police.domain.config_sections import WorldTerms
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.config_lock import ConfigLockAuthenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator

KEY_ID = KeyId("mars777-test")


def digester() -> ConfigLockAuthenticator:
    """The production adapter that already implements `ConfigDigestPort`.

    Built from the same keyed authenticator the session builders provision, so
    a digest computed here is the one production would compute.
    """
    provider = HmacSha256Provider({KEY_ID.value: b"config-digest-test-key"})
    return ConfigLockAuthenticator(KeyedAuthenticator(AuthProfile.HMAC_SHA256, KEY_ID, provider))


def runtime(group_id: str, sub_game: int = 1) -> ConfigNegotiationRuntime:
    return ConfigNegotiationRuntime(
        group_id, sub_game, 200000, PROFILES, digester(), default_scent_model()
    )


def test_the_byte_wise_lower_group_id_opens_the_exchange() -> None:
    assert initial_proposer(config()) == GROUP_B
    assert GROUP_B < GROUP_A


def test_the_opener_is_not_the_group_a_slot() -> None:
    """The lower id sits in `group_b` here, which is exactly the point."""
    assert config().agreed_between[0] == GROUP_A
    assert initial_proposer(config()) != config().agreed_between[0]


def test_the_rule_holds_when_the_ids_are_swapped_between_slots() -> None:
    swapped = replace(config(), agreed_between=(GROUP_B, GROUP_A))
    assert initial_proposer(swapped) == GROUP_B


def test_the_opener_may_send_and_the_other_side_may_not() -> None:
    proposal = runtime(GROUP_B).propose(config(), opening=True)
    assert proposal.sub_game == 1
    assert proposal.profiles == PROFILES
    with pytest.raises(LocalDefectError):
        runtime(GROUP_A).propose(config(), opening=True)


def test_both_peers_may_counter_propose() -> None:
    assert runtime(GROUP_A).propose(config(), opening=False).config == config()
    assert runtime(GROUP_B).propose(config(), opening=False).config == config()


def test_a_non_party_may_not_propose() -> None:
    with pytest.raises(LocalDefectError):
        runtime("GROUP-ZZ").propose(config(), opening=False)


def test_an_inbound_opening_from_the_wrong_side_is_stale() -> None:
    proposal = runtime(GROUP_A).propose(config(), opening=False)
    with pytest.raises(StaleMessageError):
        runtime(GROUP_B).accept(proposal, GROUP_A, opening=True)


def test_a_proposal_for_another_sub_game_is_stale() -> None:
    proposal = runtime(GROUP_B, 2).propose(config(), opening=True)
    with pytest.raises(StaleMessageError):
        runtime(GROUP_A, 1).accept(proposal, GROUP_B, opening=True)


def test_a_proposal_from_ourselves_is_stale() -> None:
    proposal = runtime(GROUP_B).propose(config(), opening=True)
    with pytest.raises(StaleMessageError):
        runtime(GROUP_B).accept(proposal, GROUP_B, opening=True)


def test_a_second_proposal_in_one_round_is_stale() -> None:
    proposal = runtime(GROUP_B).propose(config(), opening=False)
    with pytest.raises(StaleMessageError):
        runtime(GROUP_A).accept(proposal, GROUP_B, opening=False, seen=frozenset({GROUP_B}))


def test_the_token_cap_is_equality_only_after_step_zero() -> None:
    lowered = replace(
        config(), network_and_league=NetworkAndLeagueTerms(30, 60, 6, 10, 2, 10, 150000)
    )
    with pytest.raises(ConfigMismatchError):
        runtime(GROUP_B).propose(lowered, opening=True)
    incoming = ConfigNegotiationRuntime(
        GROUP_B, 1, 150000, PROFILES, digester(), default_scent_model()
    ).propose(lowered, opening=True)
    with pytest.raises(ConfigMismatchError) as failure:
        runtime(GROUP_A).accept(incoming, GROUP_B, opening=True)
    assert failure.value.error_id == "E-CONFIG-MISMATCH"


def test_a_differing_series_convention_has_its_own_identity() -> None:
    switched = replace(PROFILES, series_convention=SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION)
    proposal = ConfigNegotiationRuntime(
        GROUP_B, 1, 200000, switched, digester(), default_scent_model()
    ).propose(config(), opening=True)
    with pytest.raises(ConventionMismatchError) as failure:
        runtime(GROUP_A).accept(proposal, GROUP_B, opening=True)
    assert failure.value.error_id == "E-NET-CONVENTION-MISMATCH"


def test_convergence_needs_equal_cores_and_equal_profiles() -> None:
    ours = runtime(GROUP_A).propose(config(), opening=False)
    theirs = runtime(GROUP_B).propose(config(), opening=True)
    assert runtime(GROUP_A).converges(ours, theirs)
    other = replace(config(), world=WorldTerms("New York", 16))
    assert not runtime(GROUP_A).converges(ours, runtime(GROUP_B).propose(other, opening=True))


def test_a_sub_game_below_the_first_is_a_local_defect() -> None:
    with pytest.raises(LocalDefectError):
        ConfigNegotiationRuntime(GROUP_A, 0, 200000, PROFILES, digester(), default_scent_model())


def test_a_sender_outside_the_agreed_parties_is_stale() -> None:
    proposal = runtime(GROUP_B).propose(config(), opening=True)
    with pytest.raises(StaleMessageError):
        runtime(GROUP_A).accept(proposal, "GROUP-ZZ", opening=True)


def test_a_differing_profile_beyond_the_convention_is_a_config_mismatch() -> None:
    from mars777_police.app.interop_profiles import ToolNameProfile

    other = replace(PROFILES, tool_name_profile=ToolNameProfile.LECTURER_REFERENCE_ALIASES)
    peer = ConfigNegotiationRuntime(GROUP_B, 1, 200000, other, digester(), default_scent_model())
    proposal = peer.propose(config(), opening=True)
    with pytest.raises(ConfigMismatchError):
        runtime(GROUP_A).accept(proposal, GROUP_B, opening=True)


def test_a_valid_opening_proposal_is_accepted() -> None:
    proposal = runtime(GROUP_B).propose(config(), opening=True)
    assert runtime(GROUP_A).accept(proposal, GROUP_B, opening=True)
    assert runtime(GROUP_A).accept(proposal, GROUP_B, opening=False, seen=frozenset())
