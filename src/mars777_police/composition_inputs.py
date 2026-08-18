"""Turning operator input into the three things composing an agent needs first.

The wire a process speaks, the keyed authenticator it trusts, and the opponent
ingress it will dial: all three come from settings and a launch document rather
than from any peer, and all three are fixed before the first byte moves.

Two statements have to agree before anything is built: the compatibility mode
the operator selected, and the profile set their launch document declared. They
are the same decision written twice, so a difference is an operator error and is
refused here - neither silently overrides the other. Overriding the document
would run a series under authorities its own artifacts do not name; overriding
the mode would serve a wire the operator did not ask for.

**The KIT context is required, not optional, in external mode.** A kit turn
numbers only its own chain and a kit greeting names only its sender, so the
sub-game, our role, our group and the flat signed terms have to arrive out of
band. A process that could not state them would have to invent them, and an
invented sub-game number silently aggregates two games into one artifact set.

Nothing here reads a message. This runs before the first byte.
"""

from dataclasses import dataclass

from .app.auth_values import AuthProfile
from .app.kit_messages import KitRole
from .app.kit_payload import PeerPayload
from .app.kit_preset import ExternalMode, external_profiles
from .app.kit_session import KitSessionContext
from .app.protocol_errors import LocalDefectError
from .composition_values import SeriesIdentity
from .infra.settings import RuntimeSettings
from .protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator
from .transport.transport_profiles import TransportEnvelopeProfile, transport_profile

KitTerms = dict[str, object]
"""The flat signed set both peers hash. JSON-native, and never our own config."""


@dataclass(frozen=True, slots=True)
class WireSelection:
    """Which envelopes this process registers and sends, and its KIT context."""

    profile: TransportEnvelopeProfile
    kit_context: KitSessionContext | None


def select_wire(
    mode: ExternalMode,
    settings: RuntimeSettings,
    identity: SeriesIdentity,
    group_id: str,
    terms: KitTerms | None,
) -> WireSelection:
    """Resolve *mode* into a wire, refusing an operator input that contradicts it."""
    expected = external_profiles(mode, settings.key_id)
    if identity.profiles != expected:
        raise LocalDefectError(
            f"the launch document's profile set does not match the selected {mode.value} mode;"
            " one of the two operator statements is wrong and neither may override the other",
        )
    profile = transport_profile(mode)
    if profile is not TransportEnvelopeProfile.KIT_EXTERNAL:
        return WireSelection(profile, None)
    if terms is None:
        raise LocalDefectError(
            "external KIT mode needs the flat signed terms out of band: they are what the"
            " game_uid derives from, and no message on that wire can supply them",
        )
    context = KitSessionContext(
        group_id,
        KitRole(settings.role.value),
        PeerPayload(terms),
        identity.first_sub_game,
    )
    return WireSelection(profile, context)


def keyed_authenticator(settings: RuntimeSettings) -> KeyedAuthenticator:
    """The one provisioned keyed authenticator this process trusts.

    Built from the settings key material and never from a peer's claim: the
    profile is fixed before the first byte arrives, which is what makes an
    algorithm substitution ineffective rather than merely detectable. It is
    unchanged by the compatibility mode - interoperability buys no discount on
    authentication, and the kit's unkeyed terms digest never substitutes for it.
    """
    return KeyedAuthenticator(
        AuthProfile.HMAC_SHA256,
        settings.key_id,
        HmacSha256Provider({settings.key_id.value: settings.secret.reveal()}),
    )


def opponent_url(settings: RuntimeSettings) -> str:
    """The opponent ingress the operator configured, or a local refusal."""
    opponent = settings.opponent
    if opponent is None:
        raise ValueError("the opponent public endpoint must be configured before composing")
    return opponent.url
