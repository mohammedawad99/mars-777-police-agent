"""Which configuration schema versions this build can actually run.

Guideline §8.1 asks the application to validate the **configuration** version's
compatibility at startup. Two peers agreeing on a string is not that: byte
identity proves they hold the same document, never that either of them can
represent it. This is the missing half - a local statement of what this build
supports, enforced where a configuration first becomes a value.
"""

import dataclasses

import config_builders as build
import pytest

from mars777_police.domain.config_schema import (
    SUPPORTED_CONFIG_SCHEMA_VERSIONS,
    UnsupportedConfigSchemaError,
    require_supported_schema_version,
)
from mars777_police.domain.config_sections import InvalidConfigSectionError
from mars777_police.protocol.config_lock import config_sha256

FIXTURE_DIGEST = "b9bdf822ecc143a4a283bbf3ae6cd3bcdba9da80b7c470a73dce404f9ce44bd8"
"""The digest of the standard fixture, unchanged by this stage."""


def test_this_build_supports_exactly_the_project_contract_version() -> None:
    """JDEC-003 / NDEC-004 name `mars777-1`; nothing else is representable."""
    assert frozenset({"mars777-1"}) == SUPPORTED_CONFIG_SCHEMA_VERSIONS


def test_the_supported_set_is_immutable() -> None:
    assert isinstance(SUPPORTED_CONFIG_SCHEMA_VERSIONS, frozenset)


def test_a_supported_version_is_returned_unchanged() -> None:
    assert require_supported_schema_version("mars777-1") == "mars777-1"


def test_an_unsupported_version_is_refused_by_its_own_identity() -> None:
    with pytest.raises(UnsupportedConfigSchemaError) as failure:
        require_supported_schema_version("mars777-2")

    assert "mars777-2" in str(failure.value)
    assert "mars777-1" in str(failure.value)


def test_an_unsupported_version_is_still_a_config_section_violation() -> None:
    """Existing callers that classify config failures keep working."""
    assert issubclass(UnsupportedConfigSchemaError, InvalidConfigSectionError)


@pytest.mark.parametrize("bad", ["", None, 1, b"mars777-1"])
def test_a_malformed_version_is_refused_before_support_is_considered(bad: object) -> None:
    with pytest.raises(InvalidConfigSectionError, match="schema_version"):
        require_supported_schema_version(bad)


def test_nothing_is_substituted_for_an_unsupported_version() -> None:
    """No default, no normalisation, no downgrade - only a refusal."""
    with pytest.raises(InvalidConfigSectionError):
        build.config(schema_version="1.2")


def test_a_configuration_cannot_exist_at_an_unsupported_version() -> None:
    with pytest.raises(UnsupportedConfigSchemaError):
        build.config(schema_version="9.9.9")


def test_replacing_the_version_on_a_valid_config_is_refused_too() -> None:
    """`dataclasses.replace` re-runs validation; there is no back door."""
    with pytest.raises(UnsupportedConfigSchemaError):
        dataclasses.replace(build.config(), schema_version="mars777-0")


def test_the_supported_configuration_still_hashes_to_its_frozen_vector() -> None:
    """The digest is bytes over the core; support is a local question."""
    assert config_sha256(build.config()).value == FIXTURE_DIGEST
