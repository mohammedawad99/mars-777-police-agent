"""What a game report is, whom it goes to, and the words the source fixed.

Ch 9 §9.3 ends the game with an automatic message to the lecturer: *"at the end
of every legal game against an opponent team ... each of the two groups is
programmed to send, itself and separately, an automatic summary message to the
lecturer via the Gmail API; it is not enough that only one side sends"*.
Appendix E rules 32, 33, 34 and 51 make that a MUST, make the report a standard
JSON structure, forbid free text, and fix the address.

**The report is an attachment, not a body.** §9.3.3: *"the game report is not
free text. It is packaged in a uniform, binding JSON structure and **sent as an
attached file** to the mail message."* Rule 34 is a prohibition with a
zero-grade sanction, so the attached bytes are the report and nothing else is.

**The attached bytes already exist.** Appendix F Table 20 names the results file
`result_<game_id>.json` and calls it *"the binding report sent by email"*. That
is the artifact `series_runtime.persist_result` already writes after a mutual
agreement, so this layer attaches it and recomputes nothing about the game.
"""

from dataclasses import dataclass
from typing import Final

REPORTS_ADDRESS: Final[str] = "rmisegal+uoh26finalgame@gmail.com"
"""Appendix F Table 20, `[agent reports address]` - the destination of the JSON
reports the agent sends automatically. Ch 9: *"this is the single and binding
address for sending the reports; it must be defined as the fixed target in the
mail-sending code of each of the two agents."* Table 20 is reference-only and
explicitly **not negotiable**, so it is a source constant rather than a setting."""

MEDIA_TYPE: Final[str] = "application/json"
"""What rule 33 requires the attachment to be: a standard JSON data structure."""


class ReportError(Exception):
    """A local reporting refusal. No peer causes it and none is told about it."""


class ReportIneligibleError(ReportError):
    """This result may not be reported yet, or may not be reported at all."""


@dataclass(frozen=True, slots=True)
class GameReport:
    """One eligible game report: its identity, and the exact bytes to attach."""

    game_id: str
    group_id: str
    role: str
    result_sha256: str
    attachment_name: str
    attachment: bytes

    def __post_init__(self) -> None:
        for name in ("game_id", "group_id", "role", "result_sha256", "attachment_name"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise ReportError(f"a report needs a non-empty {name}")
        if type(self.attachment) is not bytes or not self.attachment:
            raise ReportError("a report needs the result document it attaches")

    @property
    def identity(self) -> str:
        """What makes two submissions the same report, for local de-duplication.

        The agreed digest, not a value invented here: a second send of the same
        agreed result is the same report, and a different result is a different
        one. Nothing about this identity reaches the binding JSON.
        """
        return f"{self.game_id}:{self.result_sha256}"


@dataclass(frozen=True, slots=True)
class ReportDelivery:
    """What the provider did with one report. Never what the game decided."""

    identity: str
    accepted: bool
    provider_message_id: str | None = None
    failure: str | None = None

    @property
    def complete(self) -> bool:
        """Whether reporting for this result may be considered done."""
        return self.accepted
