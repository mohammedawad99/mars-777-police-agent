"""Police agent package for the 2026 Distributed Police-Thief P2P project.

Holds the identity constants that prove role and group separation, and the
software version authority's public rendering. The behaviour lives in the layers
below - `domain`, `app`, `protocol`, `transport`, `infra` - and the one surface
an external caller is meant to import is `mars777_police.sdk`.

Nothing heavy is imported here on purpose: importing the package must not drag in
a transport framework or a game engine.
"""

from typing import Final

from .shared.version import VERSION

__all__ = [
    "GROUP_CODE",
    "ROLE",
    "VALID_ROLES",
    "__version__",
    "is_role",
]

__version__: Final[str] = VERSION.pep440
"""The software version, rendered for packaging. Authority: `shared.version`."""

GROUP_CODE: Final[str] = "MaRs-777"
"""Exact, case-sensitive group code. Must never be altered."""

ROLE: Final[str] = "POLICE"
"""This repository's fixed competitive role: POLICE or THIEF."""

VALID_ROLES: Final[frozenset[str]] = frozenset({"POLICE", "THIEF"})
"""The only legal role identifiers."""


def is_role(candidate: str) -> bool:
    """Return True only if *candidate* exactly equals this repository's role."""
    return candidate == ROLE
