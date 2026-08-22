"""The one software version this repository has, written two ways.

The excellence guideline §8.1 requires explicit version tracking whose **initial
value is 1.00**, held at `src/<pkg>/shared/version.py`. `1.00` is not a
PEP-440-stable string - the packaging rules normalise it to `1.0` - so declaring
that literal in `pyproject.toml` would publish distribution metadata that
disagrees with the declaration, which is two truths where the guideline asks for
one.

**So the value is stored once and rendered twice.** `guideline` is the literal
the guideline names; `pep440` is what packaging tools may safely round-trip. They
cannot drift, because neither is stored.

**This module owns the software version and nothing else.** The negotiated
configuration's own version, the interoperability pin and the wire profiles are
different concepts with different owners, and conflating them here would make a
local packaging fact look like a peer contract.

It imports nothing of ours on purpose: every layer may depend on it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _installed
from typing import Final

DISTRIBUTION: Final[str] = "mars-777-police-agent"
"""The installed distribution this source tree is supposed to be."""


class SoftwareVersionError(Exception):
    """This process is not the software it thinks it is.

    Raised only for a **local** integrity failure - a stale installed
    distribution shadowing the source tree, or a build whose metadata disagrees
    with the authority. It says nothing about any peer, and no peer can cause it.
    """


@dataclass(frozen=True, slots=True)
class SoftwareVersion:
    """A `MAJOR.MINOR` software version, validated at construction."""

    major: int
    minor: int

    def __post_init__(self) -> None:
        for name in ("major", "minor"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise SoftwareVersionError(f"{name} must be a non-negative int")

    @property
    def guideline(self) -> str:
        """The zero-padded rendering the guideline's table names (`1.00`)."""
        return f"{self.major}.{self.minor:02d}"

    @property
    def pep440(self) -> str:
        """The packaging rendering, stable under normalisation (`1.0`)."""
        return f"{self.major}.{self.minor}"


VERSION: Final[SoftwareVersion] = SoftwareVersion(1, 1)
"""This software's version.

Started at the guideline's initial `1.00`. Raised to `1.01` when the automatic
Gmail reporting defect was corrected after the `v1.0-submission` release: that
release satisfied Appendix E rule 32 only if an operator ran the report command,
which is not "automatic", so the behaviour of a finished series genuinely
changed and a published version had to change with it.

**Minor, not patch**, because this authority is `MAJOR.MINOR` by construction -
the guideline names that form and `SoftwareVersion` has no patch component.
Inventing one during a freeze to make the number look smaller would be inventing
policy retroactively.
"""


def verify_installation(*, lookup: Callable[[str], str] | None = None) -> None:
    """Refuse to run as a distribution that is not this source tree.

    *lookup* is injected so the failure paths are reachable without installing a
    wrong build; `None` means the real installed metadata, which is the only
    thing worth checking in production.
    """
    reader = _installed if lookup is None else lookup
    try:
        found = reader(DISTRIBUTION)
    except (PackageNotFoundError, LookupError) as failure:
        raise SoftwareVersionError(
            f"{DISTRIBUTION} is not installed; expected version {VERSION.pep440}"
        ) from failure
    if found != VERSION.pep440:
        raise SoftwareVersionError(
            f"{DISTRIBUTION} is installed as {found}, but this source is {VERSION.pep440}"
        )
