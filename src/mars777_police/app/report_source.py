"""Reading a stored result document strictly enough to report it.

The reporting command runs after a series, often in a later process, so the
authority it consults is the **artifact on disk** rather than a live runtime.
That artifact is not a weaker authority: `series_runtime.persist_result` refuses
to write it until `ResultExchange.is_agreed` holds and only then advances the
machine to `REPORT_READY`, so a `result_` file existing at all is this side's
record that the phase was reached and the agreement happened.

**Both facts are still checked, not inferred.** A document that does not carry
`mutual_agreement: true` and a `result_sha256` is refused, because a report
built from one would be exactly what Appendix E rule 35 sanctions - and because
the file may have been written by something other than this software.

**Nothing is recomputed.** The winner, the scores, the outcome and the digest
are read as facts; this module verifies their presence and never their value.
"""

from collections.abc import Mapping

from .protocol_values import Sha256Digest
from .report_values import ReportIneligibleError

AGREEMENT = "mutual_agreement"
DIGEST = "result_sha256"
REPORTED_BY = "reported_by"
GAME_ID = "game_id"


def require_agreed(document: Mapping[str, object], source: str) -> None:
    """Refuse a result document that does not record a completed agreement."""
    if document.get(AGREEMENT) is not True:
        raise ReportIneligibleError(
            f"{source} does not record a mutual agreement; Appendix E rule 35 makes"
            " agreement the condition for reporting, and a report without one is"
            " what it sanctions"
        )


def text_of(document: Mapping[str, object], field: str, source: str) -> str:
    """One required text field, or a refusal naming the field and the file."""
    value = document.get(field)
    if type(value) is not str or not value:
        raise ReportIneligibleError(f"{source} has no usable {field!r}")
    return value


def digest_of(value: str) -> Sha256Digest:
    """Return *value* as a typed digest, or refuse the result as unreportable.

    Refused here rather than carried onward as bare text: a digest read from a
    document somebody else may have written gets the same shape check every
    other artifact reader in this project applies.
    """
    try:
        return Sha256Digest(value)
    except Exception as failure:
        raise ReportIneligibleError(f"the stored result digest is unusable: {failure}") from None


def reportable_facts(document: Mapping[str, object], source: str) -> tuple[str, str, Sha256Digest]:
    """The `(game_id, reported_by, result_sha256)` an eligible result carries."""
    require_agreed(document, source)
    return (
        text_of(document, GAME_ID, source),
        text_of(document, REPORTED_BY, source),
        digest_of(text_of(document, DIGEST, source)),
    )
