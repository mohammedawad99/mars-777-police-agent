"""The outgoing message carries the report and nothing a grader could misread.

Appendix E rule 34 is a prohibition with a zero-grade sanction: the completion
report goes **only as an attached JSON file**, never as free text. `PRD07-FR-143`
locks that further - *"free-text/plaintext-only reports, prose reformatting, or
an **arbitrary email-body representation** are forbidden"* - and `PRD07-AC-032`
requires a prose-body report to be rejected before sending.

So the ruling this file enforces is **attachment-only**: the message has exactly
one leaf part, it is the result document, and no `text/plain` or `text/html`
part exists at all. A future "Hello, attached is…", a friendly banner, or the
JSON copied into the body must fail here immediately.
"""

import email
import hashlib
import json

import report_fixtures as fix

from mars777_police.app.report_message import message_bytes
from mars777_police.app.report_values import MEDIA_TYPE, REPORTS_ADDRESS

FORBIDDEN_TYPES = ("text/plain", "text/html", "text/markdown")


def parsed() -> email.message.Message:
    """The finished outgoing message, read back the way a provider reads one."""
    return email.message_from_bytes(message_bytes(fix.report()))


def leaves() -> list[email.message.Message]:
    """Every non-multipart part actually present in the serialised message."""
    return [one for one in parsed().walk() if not one.is_multipart()]


def test_the_message_has_exactly_one_leaf_part() -> None:
    assert len(leaves()) == 1


def test_that_one_part_is_the_result_attachment() -> None:
    only = leaves()[0]

    assert only.get_content_type() == MEDIA_TYPE
    assert only.get_filename() == f"result_{fix.GAME_ID}.json"
    assert "attachment" in str(only.get("Content-Disposition"))


def test_no_textual_body_part_exists_in_any_form() -> None:
    present = {one.get_content_type() for one in leaves()}

    assert present.isdisjoint(FORBIDDEN_TYPES)


def test_no_prose_survives_anywhere_in_the_serialised_message() -> None:
    """Catches a banner smuggled into a header or an extra part alike."""
    raw = message_bytes(fix.report()).decode()

    for prose in ("Hello", "Dear", "Regards", "Thanks", "please", "attached is", "```"):
        assert prose not in raw


def test_the_report_identifiers_are_not_duplicated_outside_the_attachment() -> None:
    """The body must not restate what the attachment already carries."""
    raw = message_bytes(fix.report())
    only = leaves()[0]
    envelope = raw.replace(only.get_payload(decode=False).encode(), b"")

    assert b"result_sha256" not in envelope
    assert b"group_id" not in envelope


def test_the_attachment_bytes_survive_the_mime_round_trip_exactly() -> None:
    report = fix.report()
    carried = leaves()[0].get_payload(decode=True)

    assert carried == report.attachment
    assert hashlib.sha256(carried).hexdigest() == hashlib.sha256(report.attachment).hexdigest()
    assert json.loads(carried)["mutual_agreement"] is True


def test_the_headers_a_provider_needs_are_still_present() -> None:
    message = parsed()

    assert message["To"] == REPORTS_ADDRESS
    assert message["Subject"]
    assert message["MIME-Version"] == "1.0"
    assert message.get_content_type() == "multipart/mixed"
