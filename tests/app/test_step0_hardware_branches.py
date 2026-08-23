"""A CPU-only participant completes Step-0 exactly like a GPU participant.

The end-to-end path, not just the projection: build the exchange, verify the
peer's, merge. A lawful declaration with no GPU must never be a second-class
one, and the merge must not care which branch either side declared.
"""

import pytest
from r16_builders import COMMIT_A, COMMIT_B, GROUP_A, GROUP_B, KEY_ID, SHARED_KEY, partial

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator


def port() -> Step0Authenticator:
    return Step0Authenticator(
        KeyedAuthenticator(
            AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
        )
    )


@pytest.mark.parametrize(
    ("ours", "theirs"),
    [(None, None), (None, 24), (24, None), (24, 24)],
    ids=["both-cpu", "we-cpu", "they-cpu", "both-gpu"],
)
def test_step0_completes_across_every_hardware_combination(
    ours: int | None, theirs: int | None
) -> None:
    local = partial(GROUP_A, COMMIT_A, vram=ours)
    peer = partial(GROUP_B, COMMIT_B, vram=theirs)
    us, them = Step0Runtime(GROUP_A, port()), Step0Runtime(GROUP_B, port())
    our_merge = us.accept(local, them.outbound(peer))
    their_merge = them.accept(peer, us.outbound(local))
    assert our_merge == their_merge
    assert our_merge.teams.is_merged


def test_a_cpu_only_participant_keeps_its_declared_hardware_through_the_merge() -> None:
    local = partial(GROUP_A, COMMIT_A, vram=None)
    peer = partial(GROUP_B, COMMIT_B, vram=24)
    merged = Step0Runtime(GROUP_A, port()).accept(
        local, Step0Runtime(GROUP_B, port()).outbound(peer)
    )
    assert merged.teams.group_a is not None and merged.teams.group_b is not None
    assert merged.teams.group_b.hardware.gpu is False
    assert merged.teams.group_b.hardware.vram_gb is None
    assert merged.teams.group_a.hardware.vram_gb == 24
