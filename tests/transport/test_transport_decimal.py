"""The production DTO path must reproduce the R17-R1 probe result exactly.

The probe proved the framework loses `Decimal("0.10")` when it crosses as a JSON
number. This file proves the **production** codec does not, all the way to the
digest - because an equal `Decimal` with different canonical text is still a
refused match.
"""

from decimal import Decimal

import pytest
from peer_ops import step0_exchange
from r16_builders import GROUP_A, GROUP_B, config

from mars777_police.app.participant_slots import slot_of
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.config_projection import config_core
from mars777_police.transport.codec_config import decode_config, encode_config
from mars777_police.transport.codec_declaration import decode_step0, encode_step0
from mars777_police.transport.wire_scalars import decimal_from_text, text_from_decimal

FIXTURE_DIGEST = "b9bdf822ecc143a4a283bbf3ae6cd3bcdba9da80b7c470a73dce404f9ce44bd8"


def test_the_two_fixed_decimals_cross_as_canonical_text() -> None:
    wire = encode_config(config())
    assert wire.pheromones.pheromone_decay == "0.10"
    assert wire.pheromones.pheromone_center_intensity == "0.9"
    assert isinstance(wire.pheromones.pheromone_decay, str)


def test_decimal_survives_the_production_codec_without_lexical_loss() -> None:
    rebuilt = decode_config(encode_config(config()))
    assert rebuilt.pheromones.pheromone_decay == Decimal("0.10")
    assert str(rebuilt.pheromones.pheromone_decay) == "0.10"


def test_the_config_digest_is_unchanged_by_transport() -> None:
    rebuilt = decode_config(encode_config(config()))
    assert config_sha256(rebuilt).value == config_sha256(config()).value == FIXTURE_DIGEST


def test_the_canonical_bytes_still_carry_a_bare_json_number() -> None:
    """Text is the *transport* form; the canonical layer is untouched."""
    raw = canonical_json_bytes(config_core(decode_config(encode_config(config()))))
    assert b'"pheromone_decay":0.10' in raw
    assert b'"pheromone_decay":"0.10"' not in raw


def test_a_trailing_zero_is_numerically_equal_and_lexically_decisive() -> None:
    """Why the digest, not equality, is the assertion that matters."""
    assert Decimal("0.10") == Decimal("0.1")
    assert text_from_decimal(Decimal("0.10")) != text_from_decimal(Decimal("0.1"))


@pytest.mark.parametrize("vram", [None, 24], ids=["cpu-only", "gpu"])
def test_hardware_decimal_survives_step0_transport(vram: int | None) -> None:
    original = step0_exchange(vram)
    slot = slot_of(GROUP_A, GROUP_B, GROUP_B)
    wire = encode_step0(original)
    sent = getattr(wire.declaration.teams, slot)
    assert sent is not None
    assert sent.hardware.cpu_freq_ghz == "3.5"
    received = getattr(decode_step0(wire).declaration.teams, slot)
    assert received is not None
    assert received.hardware.cpu_freq_ghz == Decimal("3.5")


def test_the_codec_never_builds_a_float() -> None:
    import inspect

    from mars777_police.transport import codec_config, wire_scalars

    for module in (codec_config, wire_scalars):
        assert "float(" not in inspect.getsource(module)
    assert decimal_from_text("0.10") == Decimal("0.10")
    assert str(decimal_from_text("0.10")) == "0.10"


def test_the_encoder_never_emits_an_exponent_form() -> None:
    assert text_from_decimal(Decimal("1E+2")) == "100"
    assert "E" not in text_from_decimal(Decimal("0.0000001"))
