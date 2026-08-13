"""Binding the agreed scent model into the lock that was already there.

SCENT-001 asks for the agreed model to be **cryptographically locked** before a
series. The 35-member config core has no room for it and must not grow, so the
model gets its own content identity and that identity travels inside the context
the existing keyed proof already covers. Nothing about the framing moves: the
same `b"config"` prefix, the same canonical bytes, the same HMAC.

The test that matters most is the last kind here: a peer that recomputes a
perfectly valid proof over a **different** model digest is still refused, because
the receiver compares the digest against the model it agreed rather than against
whatever arrived signed.
"""

import dataclasses

import pytest
from r16_builders import GAME_ID, GAME_UID, PROFILES, config
from session_builders import SUB_GAME, locker

from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.peer_pregame_messages import ConfigLockContext, ConfigLockEvidence
from mars777_police.app.protocol_errors import AuthFailureError, ConfigMismatchError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.scent_kernel import ScentKernel
from mars777_police.domain.scent_model import ScentModelAgreement
from mars777_police.domain.scent_model_default import FIGURE_4_WEIGHTS, default_scent_model
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import config_sha256, lock_context_core

GOLDEN = "e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600"
CONFIG_VECTOR = config_sha256(config()).value
"""The existing 35-member core's digest, captured before the model was bound."""


def alternate() -> ScentModelAgreement:
    """A valid, still-radial model that is simply not the one we agreed."""
    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        rows[row][col] = "0.03"
    return dataclasses.replace(default_scent_model(), kernel=ScentKernel.from_rows(rows))


def lock(model: ScentModelAgreement | None = None, shared: object = None) -> ConfigLockRuntime:
    """A real lock runtime for one round, agreeing on *model*."""
    adapter = shared or locker()
    return ConfigLockRuntime(
        GAME_ID, GAME_UID, SUB_GAME, PROFILES, adapter, adapter, model or default_scent_model()
    )


def context_of(model: ScentModelAgreement) -> ConfigLockContext:
    """The lock context a side holding *model* would build for this config."""
    return lock(model).context_for(locker().digest(config()))


def test_the_context_carries_the_agreed_model_identity() -> None:
    built = lock().context_for(locker().digest(config()))
    assert built.scent_model_sha256.value == GOLDEN
    assert built.config_sha256.value == CONFIG_VECTOR


def test_the_digest_is_derived_locally_through_the_existing_port() -> None:
    """Never received: the runtime asks its own digest port for it."""
    assert lock().scent_model_sha256 == locker().scent_model_digest(default_scent_model())
    assert lock(alternate()).scent_model_sha256.value != GOLDEN


def test_the_thirty_five_member_config_keeps_its_own_digest() -> None:
    """Binding the model must not change what `config_sha256` means."""
    assert config_sha256(config()).value == CONFIG_VECTOR
    assert context_of(default_scent_model()).config_sha256 == context_of(alternate()).config_sha256


def test_the_same_config_with_a_different_model_changes_only_the_model_digest() -> None:
    ours, theirs = context_of(default_scent_model()), context_of(alternate())
    assert ours.config_sha256 == theirs.config_sha256
    assert ours.scent_model_sha256 != theirs.scent_model_sha256


def test_a_different_model_changes_the_authenticated_bytes() -> None:
    ours = canonical_json_bytes(lock_context_core(context_of(default_scent_model())))
    theirs = canonical_json_bytes(lock_context_core(context_of(alternate())))
    assert ours != theirs
    assert b"scent_model_sha256" in ours


def test_a_different_model_changes_the_keyed_proof() -> None:
    adapter = locker()
    assert adapter.prove(context_of(default_scent_model())) != adapter.prove(
        context_of(alternate())
    )


def test_the_same_model_rebuilt_independently_proves_identically() -> None:
    adapter = locker()
    first, second = context_of(default_scent_model()), context_of(default_scent_model())
    assert first == second
    assert adapter.prove(first) == adapter.prove(second)


def test_the_lock_core_binds_exactly_the_six_members() -> None:
    core = lock_context_core(context_of(default_scent_model()))
    assert set(core) == {
        "game_id",
        "game_uid",
        "sub_game",
        "config_sha256",
        "profiles",
        "scent_model_sha256",
    }
    assert core["scent_model_sha256"] == GOLDEN


def evidence_for(model: ScentModelAgreement, shared: object) -> ConfigLockEvidence:
    """Real evidence from a peer that agreed *model*, proved with *shared*."""
    return lock(model, shared).outbound(config())


def test_matching_evidence_is_accepted() -> None:
    shared = locker()
    lock(shared=shared).accept(evidence_for(default_scent_model(), shared), shared.digest(config()))


def test_evidence_for_a_different_model_is_refused() -> None:
    """A peer that agreed one model and locked another - with a valid proof."""
    shared = locker()
    with pytest.raises(ConfigMismatchError, match="not the one this side agreed"):
        lock(shared=shared).accept(evidence_for(alternate(), shared), shared.digest(config()))


def test_a_mutated_digest_with_a_stale_proof_fails_authentication_first() -> None:
    shared = locker()
    real = evidence_for(default_scent_model(), shared)
    tampered = ConfigLockEvidence(
        dataclasses.replace(real.context, scent_model_sha256=Sha256Digest("a" * 64)), real.auth
    )
    with pytest.raises(AuthFailureError, match="did not verify"):
        lock(shared=shared).accept(tampered, shared.digest(config()))


def test_the_config_digest_check_keeps_its_own_identity() -> None:
    shared = locker()
    with pytest.raises(ConfigMismatchError, match="peer config digest differs"):
        lock(shared=shared).accept(
            evidence_for(default_scent_model(), shared), Sha256Digest("b" * 64)
        )
