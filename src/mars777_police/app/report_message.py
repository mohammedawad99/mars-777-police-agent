"""The exact message a report becomes, built the same way on every platform.

Appendix E rule 34 forbids sending the completion report as free text and
permits it **only as an attached JSON file**, so the structure is fixed: a
multipart message whose one attachment is the result document byte-for-byte,
beside a body that carries no report content and no prose.

**No subject is specified anywhere in the source.** Chapter 9, Appendix E and
Appendix F are silent, and Appendix A shows `subject` only as a parameter of an
illustrative function. It is therefore source-open, and the project fixes one
deterministic minimal subject rather than inventing a sentence per send.

**Header injection is refused, not escaped.** A carriage return or newline
inside a header value would let a crafted `game_id` append headers of its own,
so every header component is validated before the message exists.

**The bytes are platform-stable.** The message is serialised with an explicit
`\\r\\n` line ending - the one RFC 2822 requires - rather than with whatever the
running platform calls a newline, so Ubuntu and Windows produce identical bytes
for identical input.
"""

from email.message import EmailMessage
from email.policy import SMTP

from .report_values import MEDIA_TYPE, REPORTS_ADDRESS, GameReport, ReportError

GROUP_CODE_PREFIX = "MaRs-777"
BOUNDARY = "----=_MaRs-777-report"
"""The fixed multipart separator, so one report always serialises to one string."""

FORBIDDEN = ("\r", "\n", "\x00")
"""What may never appear in a header component. Refused rather than stripped."""


def safe_header(value: str, name: str) -> str:
    """Return *value* if it can be a header component, or refuse it by name."""
    if type(value) is not str or not value.strip():
        raise ReportError(f"the {name} header must be non-empty text")
    for bad in FORBIDDEN:
        if bad in value:
            raise ReportError(f"the {name} header may not contain a control character")
    return value


def subject_for(report: GameReport) -> str:
    """`MaRs-777 <role> result <game_id>` - deterministic, and source-open.

    Minimal on purpose: it names the group, which side of the pair sent it, and
    the game, so a grader can attribute and sort reports without opening one. It
    carries no score, no board state and no secret.
    """
    role = safe_header(report.role, "subject role")
    game = safe_header(report.game_id, "subject game_id")
    return f"{GROUP_CODE_PREFIX} {role} result {game}"


def body_for(report: GameReport) -> str:
    """The covering text: identifiers only, never the report and never prose.

    Rule 34 makes the attachment the report, so this body must not look like
    one. It repeats only identifiers that are already inside the attachment, in
    a fixed order, with no greeting, no commentary and no signature.
    """
    return (
        f"game_id: {report.game_id}\n"
        f"group_id: {report.group_id}\n"
        f"role: {report.role}\n"
        f"result_sha256: {report.result_sha256}\n"
        f"attachment: {report.attachment_name}\n"
    )


def message_for(report: GameReport) -> EmailMessage:
    """The complete message: fixed recipient, fixed subject, one JSON attachment."""
    message = EmailMessage()
    message["To"] = safe_header(REPORTS_ADDRESS, "To")
    message["Subject"] = subject_for(report)
    message.set_content(body_for(report), subtype="plain", charset="utf-8")
    subtype = MEDIA_TYPE.split("/", 1)[1]
    message.add_attachment(
        report.attachment,
        maintype="application",
        subtype=subtype,
        filename=safe_header(report.attachment_name, "attachment filename"),
    )
    _fix_boundary(message, report)
    return message


def _fix_boundary(message: EmailMessage, report: GameReport) -> None:
    """Replace the random separator with the fixed one, refusing a collision.

    A separator that also occurs inside the attachment would end the part early
    and corrupt the report, so it is refused rather than worked around - which
    is also what RFC 2046 requires of a boundary.
    """
    if BOUNDARY.encode() in report.attachment:
        raise ReportError("the result document contains the multipart separator")
    message.set_boundary(BOUNDARY)


def message_bytes(report: GameReport) -> bytes:
    """The serialised message, with RFC 2822 line endings on every platform."""
    return message_for(report).as_bytes(policy=SMTP)
