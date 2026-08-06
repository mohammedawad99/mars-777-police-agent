"""Police agent package for the 2026 Distributed Police-Thief P2P project.

Foundation only. Holds the identity constants used to prove role and group
separation. No game, protocol, networking, cryptography, or strategy logic
lives here yet.
"""

from typing import Final

__version__: Final[str] = "0.0.0"
"""Foundation version. Bumped once real behavior is introduced."""

GROUP_CODE: Final[str] = "MaRs-777"
"""Exact, case-sensitive group code. Must never be altered."""

ROLE: Final[str] = "POLICE"
"""This repository's fixed competitive role: POLICE or THIEF."""

VALID_ROLES: Final[frozenset[str]] = frozenset({"POLICE", "THIEF"})
"""The only legal role identifiers."""


def is_role(candidate: str) -> bool:
    """Return True only if *candidate* exactly equals this repository's role."""
    return candidate == ROLE
