"""Which of a group's two processes sends its one completion report.

Appendix E rule 35 credits a group for **its own** report and scores a series
with a missing *or contradictory* one **0 for both groups**. A group that sends
two reports is therefore taking a real risk for no gain, and a group that assumes
"whoever finished" will be exactly one process is relying on something that
stopped being true when the series started alternating roles.

`report_dispatch` used to argue that `SeriesConvention.FIXED_ROLE` made exactly
one MaRs-777 process reachable. Under the agreed counted convention -
`REFERENCE_ODD_EVEN_ALTERNATION` - **both** role backends run, both play three
sub-games, and both reach the end of the series. The old argument no longer
holds, so ownership has to be decided rather than inherited.

It is decided by the schedule, not by naming a repository: the backend that owns
the **final** sub-game is the one the series settlement is routed to, so it is
the one holding the agreed result at the moment a report becomes lawful. Under
our agreement - MaRs-777 police first - that is the thief backend, and if the
agreed first role ever flipped the owner would follow it rather than silently
become wrong.
"""

from .kit_messages import KitRole
from .kit_schedule import SUB_GAMES, role_for


def reporting_role(first_role: KitRole) -> KitRole:
    """The role that owns the group's single completion report."""
    return role_for(first_role, SUB_GAMES)


def reports_for_group(first_role: KitRole, ours: KitRole) -> bool:
    """Whether the process running *ours* is this group's reporter."""
    return reporting_role(first_role) is ours
