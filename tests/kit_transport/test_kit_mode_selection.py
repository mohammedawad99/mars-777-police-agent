"""Choosing the wire before anything is built, and never after.

A profile cannot be negotiated by the very messages whose encoding it governs,
so the selection is out of band: an operator option resolves an `ExternalMode`,
the mode resolves a `TransportEnvelopeProfile`, and the profile decides the tool
surface a process registers and the arguments its client sends. After that the
process has exactly one interpretation of the wire for its whole life.

Nothing below probes. There is no "try strict, then KIT", no key sniffing and no
downgrade after a failure - each of which turns an integrity failure into a
silent compatibility story.
"""

import asyncio
from pathlib import Path

import composed_builders as build
import pytest
from kit_builders import kit_turn
from peer_ops import commitment

from mars777_police.app.kit_preset import ExternalMode, external_profiles
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.composition import compose_agent
from mars777_police.transport.call_arguments import kit_call, strict_arguments
from mars777_police.transport.codec_turn import encode_commitment
from mars777_police.transport.peer_transport import FastMcpPeerTransport
from mars777_police.transport.transport_profiles import TransportEnvelopeProfile, transport_profile


def test_each_external_mode_resolves_exactly_one_transport_profile() -> None:
    assert (
        transport_profile(ExternalMode.STRICT_INTERNAL) is TransportEnvelopeProfile.STRICT_PROJECT
    )
    assert transport_profile(ExternalMode.KIT_CORE_V1) is TransportEnvelopeProfile.KIT_EXTERNAL


def test_the_internal_default_is_strict_so_existing_flows_never_switch() -> None:
    composition = build.compose()

    assert composition.transport_profile is TransportEnvelopeProfile.STRICT_PROJECT
    assert composition.peer_client.profile is TransportEnvelopeProfile.STRICT_PROJECT


def test_selecting_the_kit_mode_reaches_the_server_and_the_client_together() -> None:
    """No dead preset: one selection, and both directions of the wire move with it."""
    composition = build.compose(mode=ExternalMode.KIT_CORE_V1)

    assert composition.transport_profile is TransportEnvelopeProfile.KIT_EXTERNAL
    assert composition.peer_client.profile is TransportEnvelopeProfile.KIT_EXTERNAL
    assert composition.kit_context is not None


def test_the_kit_mode_also_reaches_the_semantic_and_result_authorities() -> None:
    composition = build.compose(mode=ExternalMode.KIT_CORE_V1)
    profiles = composition.identity.profiles

    assert profiles == external_profiles(ExternalMode.KIT_CORE_V1, profiles.key_id)
    assert profiles.commitment_codec.value == "KIT_CORE_COMMITMENT_V1"
    assert profiles.result_profile.value == "KIT_CORE_RESULT_V1"


def test_a_launch_document_that_contradicts_the_selected_mode_is_refused() -> None:
    """The operator's two statements must agree; neither silently overrides the other."""
    settings = build.settings_for(build.ActorRole.POLICE, "https://opponent.example/mcp")
    identity = build.identity_for(build.GROUP_A, "group_a")

    with pytest.raises(LocalDefectError):
        compose_agent(settings, identity, build.GROUP_A, ExternalMode.KIT_CORE_V1)


def test_external_mode_without_the_agreed_terms_refuses_to_compose() -> None:
    """The uid derives from the flat terms, and no message on that wire carries them."""
    settings = build.settings_for(build.ActorRole.POLICE, "https://opponent.example/mcp")
    identity = build.identity_for(build.GROUP_A, "group_a", ExternalMode.KIT_CORE_V1)

    with pytest.raises(LocalDefectError):
        compose_agent(settings, identity, build.GROUP_A, ExternalMode.KIT_CORE_V1)


def test_a_strict_client_refuses_to_send_a_kit_message() -> None:
    """Refused where the arguments are built, so nothing reaches a socket."""
    transport = FastMcpPeerTransport(build.compose().peer_client)

    with pytest.raises(LocalDefectError):
        asyncio.run(transport.send_kit(kit_turn()))


def test_a_kit_client_refuses_to_send_a_strict_envelope() -> None:
    client = build.compose(mode=ExternalMode.KIT_CORE_V1).peer_client

    with pytest.raises(LocalDefectError):
        strict_arguments("commitment", encode_commitment(commitment()), client.profile)


def test_the_client_never_changes_its_mind_after_construction() -> None:
    """One process, one interpretation - there is no setter and no mid-series switch."""
    client = build.compose().peer_client

    with pytest.raises(AttributeError):
        client.profile = TransportEnvelopeProfile.KIT_EXTERNAL


def test_the_encoder_is_the_only_owner_of_the_kit_argument_shape() -> None:
    """`transport/client.py` holds the session and the deadline, never the wire shape."""
    from mars777_police.transport import client as client_module

    source = Path(client_module.__file__).read_text(encoding="utf-8")

    assert "smell_grid" not in source
    assert "win_claim" not in source
    assert kit_call(kit_turn())[0] == "receive_turn"
