"""Three places name this software's version; a guard keeps them one truth.

`pyproject.toml` cannot import a runtime constant without a dynamic-version
backend, and migrating the build backend to get one would be a large change for
a small guarantee. The declaration therefore stays a literal, and this test is
the mechanism that stops it drifting from the authority.
"""

import tomllib
from importlib.metadata import version as installed
from pathlib import Path

import mars777_police
from mars777_police.shared.version import DISTRIBUTION, VERSION

ROOT = Path(__file__).resolve().parents[2]


def declared() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert isinstance(project, dict)
    return project


def test_pyproject_declares_the_authoritys_packaging_rendering() -> None:
    assert declared()["version"] == VERSION.pep440


def test_pyproject_names_the_distribution_the_authority_names() -> None:
    assert declared()["name"] == DISTRIBUTION


def test_the_package_dunder_version_is_the_authority() -> None:
    assert mars777_police.__version__ == VERSION.pep440


def test_the_installed_distribution_agrees_with_the_authority() -> None:
    assert installed(DISTRIBUTION) == VERSION.pep440


def test_the_package_exports_its_public_names_deliberately() -> None:
    """Guideline §14.2 recommends `__all__` and `__version__` in `__init__.py`."""
    assert "__version__" in mars777_police.__all__
    assert "GROUP_CODE" in mars777_police.__all__


def test_the_negotiated_config_schema_version_is_a_separate_concept() -> None:
    """§8.1's config-version row is the peer contract, not this software."""
    from mars777_police.domain.negotiated_config import NegotiatedConfig

    fields = {field.name for field in NegotiatedConfig.__dataclass_fields__.values()}
    assert "schema_version" in fields
    assert VERSION.pep440 not in fields
