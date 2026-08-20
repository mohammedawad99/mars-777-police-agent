"""Sending one eligible game report, and deciding nothing else at all.

The division is the one `API_BOUNDARIES.md` already uses: the application owns
**what** may be reported and **when**; infrastructure owns **how** Gmail sends
it. So `ReportSenderPort` names the second half without letting OAuth, HTTP or a
provider client type reach this layer - the port takes bytes and returns an
identifier.

**The port lives here rather than in `app.ports`** for the reason `StrategyPort`
and `HintPort` do: that module is the register of the Stage-4E-R16 protocol
adapters, and a reporting seam with one consumer reads better beside it.

**Nothing here decides a game fact.** The winner, the scores, the outcome and
the agreement were settled before a report existed; this service checks
eligibility, builds the message the source specifies, hands it to the gate, and
reports what the provider said. A provider failure is a delivery status - it
never rewrites a result.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from .report_message import message_bytes
from .report_values import GameReport, ReportDelivery, ReportError

T = TypeVar("T")

SEND_REPORT = "gmail.send_report"
"""The Gatekeeper operation identity this reporting path is configured under."""


class ReportSenderPort(Protocol):
    """Somewhere a fully-built message can be handed to a mail provider."""

    def send(self, message: bytes) -> str:
        """Send *message* and return the provider's identifier for it.

        Raises on any provider or transport failure. The bytes are already the
        complete RFC 2822 message; the adapter adds no header and no content.
        """
        ...


@dataclass(slots=True)
class ReportService:
    """The one path a game report takes from an agreed result to a provider."""

    sender: ReportSenderPort
    gate: Callable[[str, Callable[[], T]], T]
    """The Gatekeeper's own `call`, injected so this service cannot bypass it."""
    delivered: dict[str, ReportDelivery] = field(default_factory=dict)

    def status_of(self, report: GameReport) -> ReportDelivery | None:
        """What this process already knows about delivering *report*."""
        return self.delivered.get(report.identity)

    def send(self, report: GameReport) -> ReportDelivery:
        """Send *report* once, through the gate, and record what happened.

        **Once**, deliberately: a second submission of an identity this process
        already delivered returns the first answer rather than mailing the
        lecturer twice. A previous *failure* is not a delivery, so a retry after
        one is a first send, not a duplicate.
        """
        settled = self.delivered.get(report.identity)
        if settled is not None and settled.accepted:
            return settled
        try:
            identifier = self.gate(SEND_REPORT, lambda: self.sender.send(message_bytes(report)))
        except ReportError:
            raise
        except Exception as failure:
            return self._record(ReportDelivery(report.identity, False, failure=_class_of(failure)))
        return self._record(ReportDelivery(report.identity, True, provider_message_id=identifier))

    def _record(self, delivery: ReportDelivery) -> ReportDelivery:
        self.delivered[delivery.identity] = delivery
        return delivery


def _class_of(failure: BaseException) -> str:
    """The failure's class name and message, which never carry a credential.

    Every credential in this project is either wrapped so it cannot be printed
    or never enters an exception at all; the adapter additionally refuses to put
    a token into a message it raises.
    """
    return f"{type(failure).__name__}: {failure}"
