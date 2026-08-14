"""Reading the disclosed scent transcript out of an untrusted document.

The same hostile JSON `audit_capture` faces, refused the same way and with the
same message prefix, because a scent row is bound to no commitment either: the
emission was never a member of `H_commit`, so the document is the peer's *story*
about what it deposited and the only thing that makes it evidence is that both
sides kept the real one.

**Absent is legacy, not empty-by-claim.** A pre-V2 document has no `scent`
member at all and still parses, returning no rows - unlike `capture`, which a
peer must state explicitly. Completeness is a runtime question, answered where
the rows are compared: a V2 session observed emissions, so no rows will not
equal the rows it observed.

**One decimal authority, one scent type.** Intensities cross as canonical
decimal text and are rebuilt through `app.decimal_text` - the same rule
`transport` delegates to - and the deposits are handed to the domain's own
`ScentEmission`, so ordering, uniqueness and positivity are checked exactly once,
where they already live. No float is constructed on this path.
"""

import re

from ..domain.config_model import InvalidScentError
from ..domain.scent_emission import ScentDeposit, ScentEmission
from .audit_json import mapping, point, refuse, text, whole
from .decimal_text import CANONICAL_DECIMAL, decimal_from_text
from .scent_records import ScentRecord
from .turn_cursor import TurnCursor


def scent_rows(document: dict[str, object]) -> tuple[ScentRecord, ...]:
    """Every disclosed scent row, as immutable values in the order given."""
    listing = document.get("scent")
    if listing is None:
        return ()
    if not isinstance(listing, list):
        raise refuse("has an unreadable 'scent' transcript")
    sub_game = whole(document, "sub_game")
    return tuple(_row(mapping(item, "scent row"), sub_game) for item in listing)


def _row(row: dict[str, object], sub_game: int) -> ScentRecord:
    """One scent row, bound to the sub-game the document identifies."""
    return ScentRecord(TurnCursor(sub_game, whole(row, "step")), _emission(row.get("emission")))


def _emission(value: object) -> ScentEmission:
    """The disclosed deposits as the one semantic emission type, or a refusal."""
    if not isinstance(value, list):
        raise refuse("scent row has no 'emission' deposits")
    try:
        return ScentEmission(tuple(_deposit(mapping(one, "scent deposit")) for one in value))
    except InvalidScentError as failure:
        raise refuse(f"scent emission is not valid: {failure}") from failure


def _deposit(deposit: dict[str, object]) -> ScentDeposit:
    """One cell and its intensity, refusing anything but canonical decimal text."""
    intensity = text(deposit, "intensity")
    if re.fullmatch(CANONICAL_DECIMAL, intensity) is None:
        raise refuse(f"carries a non-canonical intensity {intensity!r}")
    cell = point(deposit.get("cell"), "scent deposit cell")
    return ScentDeposit(cell, decimal_from_text(intensity))
