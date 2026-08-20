"""The screening subset: chosen before any candidate outcome existed.

Exploring three candidates over the whole development set costs four full
sweeps. A screen cuts that, but only if it is chosen **blind** - so membership
is a pure function of `scenario_id`, and nothing about outcomes, families or
"interesting games" enters the choice.

    member(scenario_id)  <=>  SHA-256("screen-v1|" + scenario_id)[:8] % 1000 < 220

That is ~22% of development, uniform over the id space, so every opponent family
and configuration family keeps its share automatically rather than by a quota
somebody tuned. The same scenarios are used for the baseline and for every
candidate, which is what makes the comparison paired.
"""

import hashlib
from typing import Final

VERSION: Final[str] = "screen-v1"
SHARE_PER_MILLE: Final[int] = 220
"""About one scenario in 4.5. Frozen before any candidate was run."""


def draw(scenario: str) -> int:
    """The scenario's position in the screening lottery. Pure and stable."""
    material = f"{VERSION}|{scenario}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % 1000


def screened(scenario: str) -> bool:
    """Whether *scenario* belongs to the screening subset."""
    return draw(scenario) < SHARE_PER_MILLE


def digest_of(scenarios: tuple[str, ...]) -> str:
    """A stable identity for one screening membership list, for the manifest."""
    chosen = sorted(one for one in scenarios if screened(one))
    return hashlib.sha256("|".join(chosen).encode()).hexdigest()
