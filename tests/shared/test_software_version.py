"""The one software-version authority, and what it refuses.

Guideline v3.00 §8.1 asks for explicit version tracking whose **initial value is
`1.00`**, stored at `src/<pkg>/shared/version.py`. It is now `1.01`: the
automatic-reporting defect corrected after `v1.0-submission` genuinely changed
what a finished series does, so the published version moved with it. The
zero-padded guideline form is not a PEP-440
stable string - `packaging` normalises it to `1.0` - so storing that literal in
`pyproject.toml` would publish distribution metadata that disagrees with the
declaration. The authority therefore stores the *value* once and renders it two
ways; there is no second version to drift.
"""

import pytest

from mars777_police.shared.version import (
    DISTRIBUTION,
    VERSION,
    SoftwareVersion,
    SoftwareVersionError,
    verify_installation,
)


def test_the_authority_starts_at_the_guideline_initial_value() -> None:
    assert SoftwareVersion(1, 1) == VERSION


def test_the_guideline_rendering_is_the_literal_the_guideline_names() -> None:
    assert VERSION.guideline == "1.01"


def test_the_packaging_rendering_is_pep_440_stable() -> None:
    from packaging.version import Version

    assert str(Version(VERSION.pep440)) == VERSION.pep440
    assert VERSION.pep440 == "1.1"


def test_a_version_is_two_non_negative_integers() -> None:
    for bad in ((-1, 0), (1, -1)):
        with pytest.raises(SoftwareVersionError):
            SoftwareVersion(*bad)


def test_a_version_refuses_a_non_integer_component() -> None:
    with pytest.raises(SoftwareVersionError):
        SoftwareVersion(1, "0")  # type: ignore[arg-type]


def test_the_distribution_name_is_this_repository() -> None:
    assert DISTRIBUTION == "mars-777-police-agent"


def test_a_matching_installation_passes() -> None:
    verify_installation(lookup=lambda _: VERSION.pep440)


def test_an_installation_that_disagrees_with_the_authority_is_refused() -> None:
    with pytest.raises(SoftwareVersionError) as failure:
        verify_installation(lookup=lambda _: "9.9")

    assert DISTRIBUTION in str(failure.value)
    assert VERSION.pep440 in str(failure.value)


def test_a_missing_installation_is_refused_rather_than_assumed_compatible() -> None:
    def absent(name: str) -> str:
        raise LookupError(name)

    with pytest.raises(SoftwareVersionError):
        verify_installation(lookup=absent)


def test_the_authority_reads_the_real_installed_metadata_by_default() -> None:
    """The default path is the installed distribution, not a fixture."""
    verify_installation()


def test_the_authority_owns_no_protocol_or_third_party_version() -> None:
    """§8.1's code version is not the config schema, the wire, or a pin."""
    from pathlib import Path

    import mars777_police.shared.version as module

    source = Path(module.__file__ or "").read_text(encoding="utf-8")
    for foreign in ("schema_version", "reference-v3", "ad655762", "fastmcp", "KIT"):
        assert foreign not in source
