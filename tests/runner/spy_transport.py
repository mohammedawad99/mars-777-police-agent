"""A narrow `PeerTransportPort` that records; it implements no protocol."""

from dataclasses import dataclass, field

from mars777_police.app.capture_values import TurnOutcome
from mars777_police.app.protocol_values import Sha256Digest

LEGAL = True
DIGEST = Sha256Digest("e" * 64)


@dataclass(slots=True)
class SpyTransport:
    """Records the exact semantic value each outbound operation sent."""

    sent: list[tuple[str, object]] = field(default_factory=list)
    legality: bool = field(default=LEGAL)
    failure: BaseException | None = field(default=None)

    def _record(self, name: str, value: object) -> None:
        if self.failure is not None:
            raise self.failure
        self.sent.append((name, value))

    def names(self) -> list[str]:
        """The operations invoked, in order."""
        return [name for name, _ in self.sent]

    async def send_step0(self, exchange: object) -> None:
        self._record("step0", exchange)

    async def send_config_proposal(self, proposal: object) -> None:
        self._record("config_proposal", proposal)

    async def send_config_lock(self, evidence: object) -> None:
        self._record("config_lock", evidence)

    async def send_commitment(self, commitment: object) -> None:
        self._record("commitment", commitment)

    async def send_acknowledgement(self, acknowledgement: object) -> None:
        self._record("acknowledgement", acknowledgement)

    async def send_reveal(self, reveal: object) -> TurnOutcome:
        self._record("reveal", reveal)
        return self.legality

    async def send_final_nonce_reveal(self, disclosure: object) -> None:
        self._record("final_nonce_reveal", disclosure)

    async def send_audit_disclosure(self, document: object) -> None:
        self._record("audit_disclosure", document)

    async def send_result_agreement(self, agreement: object) -> Sha256Digest:
        self._record("result_agreement", agreement)
        return DIGEST
