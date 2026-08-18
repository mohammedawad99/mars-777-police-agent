"""The one boundary a development friendly must never be able to cross.

The pinned kit's `SHA256(canonical(terms)|nonce)` is an **unkeyed content
agreement**: anyone holding the terms and the nonce recomputes it, so it proves
both sides read the same fourteen values and nothing about who is speaking. The
book requires Step-0 to be cryptographically authenticated with a pre-supplied
key, and this project satisfies that with `HMAC_SHA256`.

A friendly run against the pinned peer is therefore authorized to play **without
that gate**, and is authorized for nothing else. `counted_capable` is a derived
property rather than a stored flag precisely so no constructor, no operator and
no later edit can set it true on a friendly run.
"""

from dataclasses import fields

import pytest

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.run_class import RunClass, RunClassification


def test_a_friendly_run_can_never_be_counted_capable() -> None:
    friendly = RunClassification.friendly(kit_terms_agreement=True)

    assert friendly.run_class is RunClass.KIT_FRIENDLY_ONLY
    assert friendly.keyed_auth_satisfied is False
    assert friendly.counted_capable is False


def test_counted_capability_is_derived_and_has_no_setter() -> None:
    """A stored flag could be set; a property computed from the facts cannot."""
    friendly = RunClassification.friendly(kit_terms_agreement=True)

    assert "counted_capable" not in {field.name for field in fields(RunClassification)}
    with pytest.raises((AttributeError, TypeError)):
        friendly.counted_capable = True


def test_a_terms_agreement_does_not_buy_counted_capability() -> None:
    """Interoperability agreement and producer authentication are different things."""
    agreed = RunClassification.friendly(kit_terms_agreement=True)
    unagreed = RunClassification.friendly(kit_terms_agreement=False)

    assert agreed.counted_capable is unagreed.counted_capable is False


def test_only_a_counted_run_with_keyed_auth_is_counted_capable() -> None:
    counted = RunClassification.counted(keyed_auth_satisfied=True)
    unauthenticated = RunClassification.counted(keyed_auth_satisfied=False)

    assert counted.counted_capable is True
    assert unauthenticated.counted_capable is False


def test_the_run_class_is_never_a_peer_facing_token() -> None:
    """The pinned wire defines no run-class value, so we serialize none."""
    friendly = RunClassification.friendly(kit_terms_agreement=True)

    assert "KIT_FRIENDLY_ONLY" not in repr(friendly.wire_view())
    assert friendly.wire_view() == {}


def test_the_counted_auth_profile_is_untouched_by_the_friendly_exception() -> None:
    """No `NONE`, no `SHA256`, no `KIT_SIGNATURE` joined the keyed-auth vocabulary."""
    assert [one.value for one in AuthProfile] == ["HMAC_SHA256", "ED25519"]
