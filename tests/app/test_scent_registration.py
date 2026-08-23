"""The agreed scent registration: what it proves, and what it deliberately cannot.

Two peers implement one pheromone physics in different code. They cannot agree
on a single digest of it - the opponent's registration document records IEEE-754
accumulation that exact `Decimal` never produces - so the identity that crosses
the wire is the registration the pairing agreed, preserved rather than re-derived.

These tests pin both halves: the external identity is carried unchanged, and the
physics behind the name is checked locally against the model this process runs.
"""

from dataclasses import replace
from decimal import Decimal

import pytest

from mars777_police.app.kit_greeting import KitGreeting
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_errors import ConfigMismatchError, LocalDefectError
from mars777_police.app.scent_registration import FAMILY, ScentRegistration, registered_model
from mars777_police.domain.config_model import ScentParams
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.infra.game_contract import scent_parameters, scent_registration
from mars777_police.protocol.kit_identity import kit_terms_digest
from mars777_police.protocol.scent_model import scent_model_sha256

AGREED = "934c220d5bf62acaa3297c6c9d723ea954c220260b02292ca17f6d5daef9f4d9"
TERMS = PeerPayload({"board_size": 7, "max_steps": 35, "setting": "Haifa"})


def context(scent: ScentRegistration | None) -> KitSessionContext:
    return KitSessionContext("MaRs-777", KitRole.POLICE, TERMS, 1, scent=scent)


def greeting(group: str, locks: tuple[tuple[str, str], ...] = ()) -> KitGreeting:
    nonce = "n" * 32
    return KitGreeting(
        TERMS,
        nonce,
        kit_terms_digest(TERMS.value, nonce),
        group,
        KitRole.THIEF,
        1,
        None,
        None,
        locks,
    )


def test_the_contract_registration_is_carried_not_recomputed() -> None:
    registration = registered_model(default_scent_model())
    assert (registration.model_id, registration.registration_sha256) == scent_registration()
    assert registration.registration_sha256 == AGREED


def test_the_external_digest_is_not_our_internal_model_digest() -> None:
    """Different domains, and neither substitutes for the other.

    Our digest covers our canonical form of our physics; the registration digest
    covers the opponent's document. Equal values here would mean one of the two
    had been derived from the other, which is exactly the confusion to avoid.
    """
    ours = scent_model_sha256(default_scent_model()).value
    assert ours != AGREED
    assert len(ours) == len(AGREED) == 64


def test_the_frozen_physics_matches_the_model_this_process_runs() -> None:
    centre, decay, size = scent_parameters()
    model = default_scent_model()
    assert Decimal(centre) == model.center_intensity
    assert Decimal(decay) == model.decay_rate
    assert size == model.field_size


def test_the_agreed_decay_compares_numerically_not_textually() -> None:
    """`0.10` and `0.1` are the same physics rendered two ways.

    Appendix F writes the decay with a trailing zero and the shared contract
    carries the JSON number; refusing on the spelling would refuse a peer that
    agrees with us completely.
    """
    _, decay, _ = scent_parameters()
    assert decay != str(default_scent_model().decay_rate)
    assert Decimal(decay) == default_scent_model().decay_rate


@pytest.mark.parametrize(
    ("field", "value"),
    [("center_intensity", Decimal("0.8")), ("decay", Decimal("0.2")), ("field_size", 7)],
    ids=["centre", "decay", "grid"],
)
def test_a_model_contradicting_the_frozen_physics_is_refused(field: str, value: object) -> None:
    """Fail closed: never declare a name whose physics this process does not play."""
    model = default_scent_model()
    params = ScentParams.__new__(ScentParams)
    object.__setattr__(params, "center_intensity", model.center_intensity)
    object.__setattr__(params, "decay", model.decay_rate)
    object.__setattr__(params, "field_size", model.field_size)
    object.__setattr__(params, field, value)
    with pytest.raises(LocalDefectError, match="must not name physics we contradict"):
        registered_model(replace(model, params=params))


def test_a_registration_digest_must_be_lowercase_hex() -> None:
    for bad in ("", "0" * 63, AGREED.upper(), "z" * 64):
        with pytest.raises(LocalDefectError, match="64 lowercase hex"):
            ScentRegistration("multiplicative_book_v1", bad)


def test_a_registration_must_name_a_model() -> None:
    with pytest.raises(LocalDefectError, match="names no model"):
        ScentRegistration("", AGREED)


def test_our_greeting_declares_the_agreed_registration() -> None:
    ours = context(registered_model(default_scent_model())).our_greeting("n" * 32, 1)
    assert ours.lock(FAMILY) == AGREED


def test_a_series_without_a_registration_declares_nothing() -> None:
    """Silence stays silence: the pinned reference peer declares no locked model."""
    assert context(None).our_greeting("n" * 32, 1).locks == ()
    assert context(None).our_greeting("n" * 32, 1).lock(FAMILY) is None


def test_a_peer_declaring_the_same_registration_is_accepted() -> None:
    session = context(registered_model(default_scent_model()))
    pairing = session.accept(greeting("s82kma9e", ((FAMILY, AGREED),)))
    assert pairing.peer_group == "s82kma9e"


def test_a_peer_that_declares_nothing_is_still_accepted() -> None:
    """Omission never refuses - forfeiting to our own guard is still forfeiting."""
    session = context(registered_model(default_scent_model()))
    assert session.accept(greeting("s82kma9e")).terms_agreed


def test_a_peer_declaring_a_different_registration_is_refused() -> None:
    session = context(registered_model(default_scent_model()))
    with pytest.raises(ConfigMismatchError, match="one game cannot carry two physics"):
        session.accept(greeting("s82kma9e", ((FAMILY, "b" * 64),)))


def test_a_series_with_no_registration_judges_no_declaration() -> None:
    """Nothing agreed means nothing to contradict, so a declared digest passes."""
    assert context(None).accept(greeting("s82kma9e", ((FAMILY, "b" * 64),))).terms_agreed


def test_another_family_is_not_read_as_the_scent_one() -> None:
    session = context(registered_model(default_scent_model()))
    assert session.accept(greeting("s82kma9e", (("wire_shape", "c" * 64),))).terms_agreed
