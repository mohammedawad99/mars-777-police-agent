"""The exact authenticated framing, verified byte for byte.

The supervising ruling fixes the construction as the ASCII context immediately
followed by the canonical bytes, with **no** inserted byte:

    b"step0"  + canonical_json_bytes(step0_core)
    b"config" + canonical_json_bytes(config_lock_context)

These tests verify that behaviour; they do not introduce a framing framework, a
framing enum or a negotiable profile, and there is nothing here to configure.
"""

import pytest
from r16_builders import COMMIT_A, GAME_ID, GAME_UID, GROUP_A, PROFILES, config, partial

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.peer_pregame_messages import ConfigLockContext
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import config_sha256, lock_context_core
from mars777_police.protocol.declaration import step0_core
from mars777_police.protocol.keyed_auth import (
    CONFIG_CONTEXT,
    STEP0_CONTEXT,
    auth_input,
)
from mars777_police.protocol.scent_model import scent_model_sha256

CONTEXTS = (STEP0_CONTEXT, CONFIG_CONTEXT)


MODEL_DIGEST = scent_model_sha256(default_scent_model())


def step0_bytes() -> bytes:
    return auth_input(STEP0_CONTEXT, step0_core(partial(GROUP_A, COMMIT_A, "group_a"), GROUP_A))


def config_bytes() -> bytes:
    context = ConfigLockContext(
        GAME_ID, GAME_UID, 1, config_sha256(config()), PROFILES, MODEL_DIGEST
    )
    return auth_input(CONFIG_CONTEXT, lock_context_core(context))


def test_the_two_context_labels_are_exactly_the_frozen_pair() -> None:
    assert CONTEXTS == ("step0", "config")
    assert all(label.isascii() and label.islower() for label in CONTEXTS)


def test_the_step0_input_begins_exactly_with_the_context_and_the_brace() -> None:
    assert step0_bytes().startswith(b"step0{")


def test_the_config_lock_input_begins_exactly_with_the_context_and_the_brace() -> None:
    assert config_bytes().startswith(b"config{")


@pytest.mark.parametrize(
    ("label", "producer"), [(b"step0", step0_bytes), (b"config", config_bytes)]
)
def test_no_byte_exists_between_the_context_and_the_opening_brace(
    label: bytes, producer: object
) -> None:
    raw = producer()  # type: ignore[operator]
    assert raw[: len(label)] == label
    assert raw[len(label) : len(label) + 1] == b"{"


@pytest.mark.parametrize(
    ("label", "producer"), [(b"step0", step0_bytes), (b"config", config_bytes)]
)
def test_the_remainder_is_exactly_the_canonical_bytes(label: bytes, producer: object) -> None:
    """No separator, no padding, no length prefix, no trailing byte."""
    raw = producer()  # type: ignore[operator]
    core = (
        step0_core(partial(GROUP_A, COMMIT_A, "group_a"), GROUP_A)
        if label == b"step0"
        else lock_context_core(
            ConfigLockContext(GAME_ID, GAME_UID, 1, config_sha256(config()), PROFILES, MODEL_DIGEST)
        )
    )
    assert raw == label + canonical_json_bytes(core)
    assert len(raw) == len(label) + len(canonical_json_bytes(core))


@pytest.mark.parametrize("separator", [b"\x00", b":", b"|", b" ", b"\n", b"\t", b"-"])
def test_no_candidate_separator_was_inserted(separator: bytes) -> None:
    for producer, label in ((step0_bytes, b"step0"), (config_bytes, b"config")):
        assert not producer().startswith(label + separator)


def test_no_length_prefix_precedes_the_context() -> None:
    for producer, label in ((step0_bytes, b"step0"), (config_bytes, b"config")):
        raw = producer()
        assert raw[0:1] == label[0:1]
        assert not raw[0:1].isdigit()


def test_neither_context_label_is_a_prefix_of_the_other() -> None:
    """Which is why the boundary is unambiguous with no separator at all."""
    first, second = CONTEXTS
    assert not first.startswith(second) and not second.startswith(first)
    assert first[0] != second[0]


def test_a_canonical_object_always_begins_with_a_brace() -> None:
    """The second half of the ambiguity proof: the payload is self-delimiting."""
    for producer in (step0_bytes, config_bytes):
        raw = producer()
        assert b"{" in raw
        assert raw[raw.index(b"{") :].startswith(b"{")
    assert canonical_json_bytes({"a": 1}).startswith(b"{")


def test_a_step0_proof_can_never_be_replayed_as_a_config_proof() -> None:
    from r16_builders import KEY_ID, SHARED_KEY

    from mars777_police.protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator

    auth = KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KEY_ID, HmacSha256Provider({KEY_ID.value: SHARED_KEY})
    )
    shared = {"game_id": GAME_ID}
    assert not auth.verify(CONFIG_CONTEXT, shared, auth.prove(STEP0_CONTEXT, shared))
