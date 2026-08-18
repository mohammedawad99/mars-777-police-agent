"""One explicit choice that selects the whole external profile, before play.

The alternative is eight independent switches an operator has to get right
together, where any one of them left on the internal default produces a peer
that agrees on everything except the bytes. So external mode is a single
selection made **before** the series, and it resolves to a frozen profile set.

`KIT_CORE_V1` is a *local* name. The pinned kit defines no such token, so it is
never serialized to a peer - the profile's own eleven members are what any
future transport would carry.
"""

import pytest

from mars777_police.app.auth_values import AuthProfile, KeyId
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.interop_profiles import ResultProfile, SeriesConvention
from mars777_police.app.kit_preset import ExternalMode, external_profiles

KEY = KeyId("mars777-k1")


def test_the_kit_preset_selects_every_kit_authority_at_once() -> None:
    profiles = external_profiles(ExternalMode.KIT_CORE_V1, KEY)

    assert profiles.commitment_codec is CommitmentCodec.KIT_CORE_COMMITMENT_V1
    assert profiles.result_profile is ResultProfile.KIT_CORE_RESULT_V1


def test_the_preset_keeps_our_keyed_authentication() -> None:
    """Interoperability never buys itself a weaker handshake."""
    profiles = external_profiles(ExternalMode.KIT_CORE_V1, KEY)

    assert profiles.auth_profile is AuthProfile.HMAC_SHA256
    assert profiles.key_id == KEY


def test_the_preset_offers_only_the_role_convention_we_can_execute() -> None:
    """One fixed role per process; alternation is not implemented anywhere yet."""
    profiles = external_profiles(ExternalMode.KIT_CORE_V1, KEY)

    assert profiles.series_convention is SeriesConvention.FIXED_ROLE


def test_the_strict_mode_keeps_every_internal_authority() -> None:
    profiles = external_profiles(ExternalMode.STRICT_INTERNAL, KEY)

    assert profiles.commitment_codec is CommitmentCodec.STRICT_PROJECT_COMMITMENT
    assert profiles.result_profile is ResultProfile.STRICT_PROJECT_RESULT


def test_the_two_modes_differ_only_where_a_profile_really_differs() -> None:
    kit = external_profiles(ExternalMode.KIT_CORE_V1, KEY)
    strict = external_profiles(ExternalMode.STRICT_INTERNAL, KEY)

    assert kit.auth_profile is strict.auth_profile
    assert kit.nonce_representation_profile is strict.nonce_representation_profile
    assert kit.commitment_codec is not strict.commitment_codec


def test_the_local_preset_name_is_never_a_peer_facing_token() -> None:
    """The kit defines no `KIT_CORE_V1`; sending one would be inventing protocol."""
    profiles = external_profiles(ExternalMode.KIT_CORE_V1, KEY)
    serialized = {
        profiles.commitment_codec.value,
        profiles.result_profile.value,
        profiles.series_convention.value,
        profiles.auth_profile.value,
    }

    assert "KIT_CORE_V1" not in serialized


def test_an_unknown_mode_cannot_be_constructed() -> None:
    with pytest.raises(ValueError):
        ExternalMode("SOMETHING_ELSE")
