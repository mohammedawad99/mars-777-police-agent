"""The façade re-exports the pregame peer types with defining-type identity."""

from mars777_police.app import peer_messages
from mars777_police.app.peer_pregame_messages import (
    ConfigLockContext,
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)

PREGAME_EXPORTS = (
    ("Step0DeclarationExchange", Step0DeclarationExchange),
    ("ConfigProposal", ConfigProposal),
    ("ConfigLockContext", ConfigLockContext),
    ("ConfigLockEvidence", ConfigLockEvidence),
)


def test_facade_exports_the_same_class_objects() -> None:
    for name, defining in PREGAME_EXPORTS:
        assert getattr(peer_messages, name) is defining


def test_facade_all_lists_every_pregame_export() -> None:
    for name, _ in PREGAME_EXPORTS:
        assert name in peer_messages.__all__


def test_facade_all_is_sorted_and_unique() -> None:
    assert peer_messages.__all__ == sorted(peer_messages.__all__)
    assert len(set(peer_messages.__all__)) == len(peer_messages.__all__)


def test_facade_does_not_leak_support_values() -> None:
    leaked = {
        "AuthProfile",
        "AuthProof",
        "KeyId",
        "Declaration",
        "GitCommitSha",
        "UtcTimestamp",
        "InteropProfileSet",
        "NegotiatedConfig",
    }
    assert not leaked & set(peer_messages.__all__)


def test_facade_defines_no_class_of_its_own() -> None:
    for name in peer_messages.__all__:
        exported = getattr(peer_messages, name)
        assert exported.__module__ != peer_messages.__name__
