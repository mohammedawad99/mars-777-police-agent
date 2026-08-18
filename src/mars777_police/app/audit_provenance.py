"""Which authority stands behind each finding, and therefore what silence costs.

The counted-clean policy asks one question of every check - *who required
this?* - because the answer decides what an undecidable result means. This is
where that question is answered, once, for every verdict the semantic reviewer
can produce.

**Exhaustive by construction.** A verdict nobody classified would arrive at the
policy with no rule attached, and there is no safe default: guessing binding
would libel lawful peers, guessing enrichment would wave through unproven
results. A test asserts the mapping covers `SemanticVerdict` completely, so a
new finding cannot be added without deciding what it costs.

**The gameplay rules are the book's.** A start cell that is not the locked one,
a trajectory that does not join up, an action the rules refuse, a barrier set
that does not match the declared placements, and the three capture-honesty
findings all come from the course book and Appendix E. Unknown there blocks a
counted result.

**Scent truthfulness is ours.** JDEC-018 re-renders a peer's emission from the
trajectory it disclosed, and a lawful KIT peer never agreed to disclose one -
so its absence must cost that peer nothing, while a contradiction remains a
finding. `CONSISTENT` is classified the same way for the same reason: it is the
absence of a complaint, not an authority that can block anything.
"""

from collections.abc import Mapping
from types import MappingProxyType

from .audit_status import CheckProvenance
from .semantic_values import SemanticVerdict

_BINDING = CheckProvenance.SOURCE_BINDING
_OURS = CheckProvenance.PROJECT_ENRICHMENT

PROVENANCE: Mapping[SemanticVerdict, CheckProvenance] = MappingProxyType(
    {
        SemanticVerdict.CONSISTENT: _OURS,
        SemanticVerdict.WRONG_START: _BINDING,
        SemanticVerdict.BROKEN_TRAJECTORY: _BINDING,
        SemanticVerdict.ILLEGAL_ACTION: _BINDING,
        SemanticVerdict.WRONG_BARRIER_SET: _BINDING,
        SemanticVerdict.FALSE_CAPTURE_CLAIM: _BINDING,
        SemanticVerdict.DISHONEST_CAPTURE_ANSWER: _BINDING,
        SemanticVerdict.FALSE_CLAIM_AFFIRMED: _BINDING,
        SemanticVerdict.DISHONEST_SCENT_EMISSION: _OURS,
    }
)
"""Every verdict, with the authority that decides what an unknown one costs."""


def provenance_of(verdict: SemanticVerdict) -> CheckProvenance:
    """The authority behind *verdict*."""
    return PROVENANCE[verdict]
