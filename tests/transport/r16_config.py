"""The Appendix-F conforming negotiated config, kept apart from the fixtures.

Split out of `r16_builders` under guideline §3.2: the declaration builders and
this table are separate concerns that happened to share a file, and the file had
grown past the 150-code-line cap. `r16_builders` re-exports `config`, so every
existing `from r16_builders import config` keeps working.

Every number here is Appendix F's. Vary one with `dataclasses.replace` rather
than editing this table, so a test that needs a different value says which.
"""

from decimal import Decimal

from mars777_police.domain.board import Position
from mars777_police.domain.config_league_sections import (
    NetworkAndLeagueTerms,
    PheromoneTerms,
    RateLimiterTerms,
)
from mars777_police.domain.config_sections import (
    BoardAndAgentsTerms,
    MovementAndBarrierTerms,
    ScoringTerms,
    WorldTerms,
)
from mars777_police.domain.negotiated_config import NegotiatedConfig

GROUP_A = "MaRs-777"
GROUP_B = "GROUP-XY"
"""The two participants, defined here and re-exported by `r16_builders`.

They live in the lower module so there is exactly one definition: a second copy
could drift, and a `config()` whose participants disagreed with the declarations
would be a fixture that quietly contradicts itself.
"""


def config() -> NegotiatedConfig:
    """Return the Appendix-F conforming config; vary it with `dataclasses.replace`."""
    return NegotiatedConfig(
        "mars777-1",
        (GROUP_A, GROUP_B),
        BoardAndAgentsTerms(7, 2, Position(3, 3), Position(0, 0), "top-left", 0),
        WorldTerms("New York", 15),
        MovementAndBarrierTerms(("N", "S", "E", "W", "STAY"), 14, 35, 35),
        ScoringTerms(20, 5, 5, 10, 2, 0),
        PheromoneTerms(Decimal("0.9"), Decimal("0.10"), 5),
        NetworkAndLeagueTerms(30, 60, 6, 10, 2, 10, 200000),
        RateLimiterTerms(30, 2, 5, 3, 100),
    )
