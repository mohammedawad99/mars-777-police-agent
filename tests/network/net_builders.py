"""Declaration fixtures whose `mcp_endpoint` is the value under test.

The R16 builders hard-code an example endpoint, which is exactly what the
declaration-before-auth lifecycle must *not* do: here the endpoint is a
parameter, so a test can prove the authenticated bytes followed it.
"""

from dataclasses import replace

from r16_builders import COMMIT_A, GAME_ID, GAME_UID, GROUP_A, KEY_ID, SHARED_KEY, START, team

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.declaration_values import Declaration, DeclarationTeams, DeclarationTimes
from mars777_police.app.public_endpoint_values import OwnPublicPeerEndpoint
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator


def authenticator() -> Step0Authenticator:
    """The real keyed Step-0 adapter, over an out-of-band shared secret."""
    return Step0Authenticator(
        KeyedAuthenticator(
            AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )
    )


def runtime(group_id: str = GROUP_A) -> Step0Runtime:
    """A real Step-0 runtime; nothing about auth is faked."""
    return Step0Runtime(group_id, authenticator())


def declaration_at(endpoint: OwnPublicPeerEndpoint) -> Declaration:
    """Our own pre-exchange snapshot, declaring exactly *endpoint*."""
    subtree = replace(team(GROUP_A, COMMIT_A), mcp_endpoint=endpoint.url)
    return Declaration(
        GAME_ID,
        GAME_UID,
        200000,
        DeclarationTimes(START, None),
        DeclarationTeams(subtree, None),
    )
