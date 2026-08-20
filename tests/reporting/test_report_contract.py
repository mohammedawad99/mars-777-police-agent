"""The exact message the source specifies, pinned as a golden vector.

Appendix E rule 34 is a prohibition with a zero-grade sanction: the completion
report goes **only** as an attached JSON file, never as free text. Rule 33 makes
the attachment a standard JSON structure, and Appendix F Table 20 names both the
file and the single address it goes to. These tests read the finished bytes, so
what is asserted is what a provider would receive.
"""

import base64
import email
import json

import report_fixtures as fix

from mars777_police.app.report_message import BOUNDARY, message_bytes, subject_for
from mars777_police.app.report_values import REPORTS_ADDRESS

GOLDEN_SUBJECT = f"MaRs-777 police result {fix.GAME_ID}"


def parsed() -> email.message.Message:
    """The built message, read back the way a mail client reads one."""
    return email.message_from_bytes(message_bytes(fix.report()))


def test_the_recipient_is_the_one_address_appendix_f_names() -> None:
    assert REPORTS_ADDRESS == "rmisegal+uoh26finalgame@gmail.com"
    assert parsed()["To"] == REPORTS_ADDRESS


def test_the_subject_is_the_documented_deterministic_one() -> None:
    assert subject_for(fix.report()) == GOLDEN_SUBJECT
    assert parsed()["Subject"] == GOLDEN_SUBJECT


def test_the_report_travels_as_an_attachment_and_not_as_the_body() -> None:
    parts = list(parsed().walk())
    attachments = [one for one in parts if one.get_filename()]

    assert len(attachments) == 1
    assert attachments[0].get_filename() == f"result_{fix.GAME_ID}.json"
    assert attachments[0].get_content_type() == "application/json"


def test_the_attached_bytes_are_the_result_document_unchanged() -> None:
    original = fix.report().attachment
    attachment = next(one for one in parsed().walk() if one.get_filename())

    carried = base64.b64decode(attachment.get_payload())

    assert carried == original
    assert json.loads(carried)["mutual_agreement"] is True


def test_the_covering_body_carries_identifiers_and_no_prose() -> None:
    body = next(one for one in parsed().walk() if one.get_content_type() == "text/plain")
    text = body.get_payload(decode=True).decode()

    assert text.splitlines()[0] == f"game_id: {fix.GAME_ID}"
    assert all(":" in line for line in text.splitlines() if line)
    for prose in ("Hello", "Dear", "Regards", "```", "please", "Thanks"):
        assert prose not in text


def test_one_report_always_serialises_to_exactly_the_same_bytes() -> None:
    once, twice = message_bytes(fix.report()), message_bytes(fix.report())

    assert once == twice
    assert BOUNDARY.encode() in once


def test_the_message_uses_rfc2822_line_endings_on_every_platform() -> None:
    raw = message_bytes(fix.report())

    assert raw.count(b"\n") == raw.count(b"\r\n")
    assert b"\r\r" not in raw


def test_no_sender_header_is_written_because_gmail_owns_it() -> None:
    assert parsed()["From"] is None
