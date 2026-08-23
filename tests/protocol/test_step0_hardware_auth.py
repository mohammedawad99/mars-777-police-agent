"""Authenticating both hardware branches, and what tampering with them costs.

A CPU-only participant is a lawful declaration, not a degraded one: it must be
projectable, authenticatable and verifiable exactly like a GPU participant. The
tamper cases work on the **projected core**, because the semantic value already
refuses the malformed hardware combinations - loosening it to manufacture a
tampered object would destroy the very rule under test.
"""

import pytest
from r16_builders import COMMIT_A, GROUP_A, KEY_ID, SHARED_KEY, partial

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.team_declaration_values import (
    HardwareDeclaration,
    InvalidTeamDeclarationError,
)
from mars777_police.protocol.declaration import Step0Authenticator, step0_core
from mars777_police.protocol.keyed_auth import STEP0_CONTEXT, HmacSha256Provider, KeyedAuthenticator


def authenticator() -> KeyedAuthenticator:
    return KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    )


def step0() -> Step0Authenticator:
    return Step0Authenticator(authenticator())


@pytest.mark.parametrize("vram", [None, 24], ids=["cpu-only", "gpu"])
def test_both_branches_build_and_verify_a_proof(vram: int | None) -> None:
    local = partial(GROUP_A, COMMIT_A, vram=vram)
    proof = step0().prove(local, GROUP_A)
    assert len(proof.value) == 64
    assert step0().verify(local, GROUP_A, proof)


def test_a_cpu_only_proof_does_not_verify_over_a_gpu_core() -> None:
    cpu = partial(GROUP_A, COMMIT_A, vram=None)
    gpu = partial(GROUP_A, COMMIT_A, vram=24)
    assert not step0().verify(gpu, GROUP_A, step0().prove(cpu, GROUP_A))
    assert not step0().verify(cpu, GROUP_A, step0().prove(gpu, GROUP_A))


def test_changing_the_vram_value_invalidates_the_existing_proof() -> None:
    """24 -> 25 is a different authenticated subject, and must fail."""
    gpu = partial(GROUP_A, COMMIT_A, vram=24)
    proof = authenticator().prove(STEP0_CONTEXT, step0_core(gpu, GROUP_A))
    tampered = step0_core(gpu, GROUP_A)
    tampered["teams"]["group_b"]["hardware"]["vram_gb"] = 25  # type: ignore[index]
    assert not authenticator().verify(STEP0_CONTEXT, tampered, proof)


def test_naming_a_gpu_without_vram_is_a_different_subject_and_fails() -> None:
    cpu = partial(GROUP_A, COMMIT_A, vram=None)
    proof = authenticator().prove(STEP0_CONTEXT, step0_core(cpu, GROUP_A))
    tampered = step0_core(cpu, GROUP_A)
    tampered["teams"]["group_b"]["hardware"]["gpu"] = "RTX 4090"  # type: ignore[index]
    assert not authenticator().verify(STEP0_CONTEXT, tampered, proof)


def test_that_tampered_combination_is_unconstructable_as_a_semantic_value() -> None:
    """Which is why the tamper had to be done on the projected core."""
    with pytest.raises(InvalidTeamDeclarationError):
        HardwareDeclaration("Linux", 8, __import__("decimal").Decimal("3.5"), 32, "RTX", None)
    with pytest.raises(InvalidTeamDeclarationError):
        HardwareDeclaration("Linux", 8, __import__("decimal").Decimal("3.5"), 32, False, 24)


@pytest.mark.parametrize("vram", [None, 24], ids=["cpu-only", "gpu"])
def test_two_peers_project_the_same_participant_to_identical_bytes(vram: int | None) -> None:
    from mars777_police.protocol.canonical import canonical_json_bytes

    ours = partial(GROUP_A, COMMIT_A, vram=vram)
    theirs = partial(GROUP_A, COMMIT_A, vram=vram)
    assert ours == theirs
    assert canonical_json_bytes(step0_core(ours, GROUP_A)) == canonical_json_bytes(
        step0_core(theirs, GROUP_A)
    )
    assert step0().verify(theirs, GROUP_A, step0().prove(ours, GROUP_A))


def test_different_hardware_produces_different_bytes() -> None:
    from mars777_police.protocol.canonical import canonical_json_bytes

    assert canonical_json_bytes(
        step0_core(partial(GROUP_A, COMMIT_A, vram=24), GROUP_A)
    ) != canonical_json_bytes(step0_core(partial(GROUP_A, COMMIT_A, vram=32), GROUP_A))
