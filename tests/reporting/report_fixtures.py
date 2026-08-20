"""Deterministic reporting material: an agreed result, and a provider that isn't real.

Every double here is unmistakably non-counted and unmistakably offline. A fake
provider answer is evidence that this code builds and classifies a request
correctly; it is never evidence that Gmail accepted anything.
"""

import json
from pathlib import Path

from mars777_police.app.gatekeeper import Gatekeeper
from mars777_police.app.report_service import ReportService
from mars777_police.app.report_values import GameReport
from mars777_police.infra.rate_limit_file import load_rate_limits

GAME_ID = "mars777-vs-groupx-2026w1-uid0001"
DIGEST = "a" * 64


def result_document(**overrides: object) -> dict[str, object]:
    """An agreed result document, shaped exactly as `result_document` writes one."""
    document: dict[str, object] = {
        "game_id": GAME_ID,
        "game_uid": "uid0001",
        "lines": [],
        "result_sha256": DIGEST,
        "mutual_agreement": True,
        "reported_by": "mars777",
    }
    document.update(overrides)
    return document


def written_result(root: Path, **overrides: object) -> Path:
    """Write a result artifact under *root* and return where it went."""
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"result_{GAME_ID}.json"
    target.write_text(json.dumps(result_document(**overrides)), encoding="utf-8")
    return target


def report(**overrides: object) -> GameReport:
    """One eligible report, built without touching a disk or a provider.

    The attachment is derived from the digest unless a test names its own, the
    way production derives both from one document: two reports that differ only
    by `result_sha256` must differ in their attached bytes too, because in a
    real run that digest **is** a field of the document being attached.
    """
    digest = overrides.get("result_sha256", DIGEST)
    fields: dict[str, object] = {
        "game_id": GAME_ID,
        "group_id": "mars777",
        "role": "police",
        "result_sha256": digest,
        "attachment_name": f"result_{GAME_ID}.json",
        "attachment": json.dumps(result_document(result_sha256=digest)).encode(),
    }
    fields.update(overrides)
    return GameReport(**fields)  # type: ignore[arg-type]


class FakeGmail:
    """A provider that records what it was handed and answers as instructed."""

    def __init__(self, answers: list[object] | None = None) -> None:
        self.answers = answers or []
        self.sent: list[bytes] = []

    def send(self, message: bytes) -> str:
        """Record the message, then return or raise whatever the test queued."""
        self.sent.append(message)
        answer = self.answers.pop(0) if self.answers else f"msg-{len(self.sent)}"
        if isinstance(answer, BaseException):
            raise answer
        return str(answer)


class Clock:
    """A monotonic clock a test advances by hand, and a sleeper that only records."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        """The current instant. It moves only when a test moves it."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Record a wait and advance the clock. Nothing real ever waits."""
        self.slept.append(seconds)
        self.now += seconds


def service(
    provider: FakeGmail, clock: Clock | None = None
) -> tuple[ReportService, Gatekeeper, Clock]:
    """A reporting service over the shipped policy and a fake provider."""
    ticking = clock or Clock()
    keeper = Gatekeeper(load_rate_limits(), monotonic=ticking.monotonic, sleeper=ticking.sleep)
    return ReportService(provider, keeper.call), keeper, ticking
