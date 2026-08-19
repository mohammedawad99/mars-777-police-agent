"""Foundation smoke tests: identity, role, and group-code integrity.

These tests guard the invariants that keep the police and thief repositories
from ever being confused for one another. They contain no game logic.
"""

import mars777_police as agent
from mars777_police.shared.version import VERSION

EXPECTED_ROLE = "POLICE"
OPPOSING_ROLE = "THIEF"


def test_package_imports() -> None:
    """The package renders the authority; it does not hold a literal of its own."""
    assert agent.__version__ == VERSION.pep440


def test_group_code_is_exact() -> None:
    # Case-sensitive: 'MaRs-777' only, never 'mars-777' or 'MARS-777'.
    assert agent.GROUP_CODE == "MaRs-777"
    assert len(agent.GROUP_CODE) == 8


def test_role_is_correct() -> None:
    assert agent.ROLE == EXPECTED_ROLE
    assert agent.ROLE in agent.VALID_ROLES


def test_role_cannot_be_confused_with_sibling() -> None:
    # A POLICE repository must never identify as THIEF.
    assert agent.ROLE != OPPOSING_ROLE
    assert agent.is_role(EXPECTED_ROLE)
    assert not agent.is_role(OPPOSING_ROLE)
