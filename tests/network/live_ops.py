"""A public peer whose handlers are the **production** runtimes, not recorders.

The R17 live harness recorded what it received, which is enough to prove a value
crossed the wire but cannot prove an error identity: a recorder never refuses
anything. Every rejection below therefore comes from the real application -
`Step0Runtime.accept` for a stale or unauthentic declaration,
`ConfigNegotiationRuntime.accept` for a differing series convention, and
`ResultExchange.accept_peer_request` for the result direction. No exception is
injected by this class.

Receipt crosses back to the test through a **harness-owned status file**, exactly
as the R17 two-process cadence does. It is not a fifth MCP tool and never
becomes one.
"""

import json
from pathlib import Path

from cadence_ops import exchange_for
from peer_ops import ILLEGAL_HINT, authenticator
from r16_builders import COMMIT_A, GAME_ID, GROUP_A, GROUP_B, PROFILES, partial

from mars777_police.app.capture_values import TurnOutcome
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.config_lock import ConfigLockAuthenticator
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.transport.inbound_session import InboundSession

TOKEN_BUDGET = 200000


class LiveOperations:
    """The remote half of the public route, answering with production behaviour."""

    def __init__(self, status: Path) -> None:
        self.status = status
        self.seen: list[str] = []
        self.local = partial(GROUP_A, COMMIT_A)
        self.step0 = Step0Runtime(GROUP_A, Step0Authenticator(authenticator()))
        self.negotiation = ConfigNegotiationRuntime(
            GROUP_A,
            1,
            TOKEN_BUDGET,
            PROFILES,
            ConfigLockAuthenticator(authenticator()),
            default_scent_model(),
        )
        self.exchange = exchange_for(GROUP_A, 200)
        self._write()

    def _write(self) -> None:
        self.status.write_text(
            json.dumps(
                {
                    "seen": self.seen,
                    "game_id": GAME_ID,
                    "verified": self.exchange.verified,
                    "peer_request_handled": self.exchange.peer_request_handled,
                    "local_digest": (
                        self.exchange.local_digest.value if self.exchange.local_digest else None
                    ),
                }
            ),
            encoding="utf-8",
        )

    def _record(self, name: str) -> None:
        self.seen.append(name)
        self._write()

    def on_step0(self, exchange: object, session: InboundSession) -> None:
        """Real Step-0 acceptance: a bad proof or a stale game refuses here."""
        self.step0.accept(self.local, exchange)  # type: ignore[arg-type]
        self._record("step0")

    def on_config_proposal(self, value: object, session: InboundSession) -> None:
        """Real negotiation acceptance: a differing series convention refuses here."""
        self.negotiation.accept(value, GROUP_B, opening=True)  # type: ignore[arg-type]
        self._record("config_proposal")

    def on_config_lock(self, value: object, session: InboundSession) -> None:
        self._record("config_lock")

    def on_commitment(self, value: object, session: InboundSession) -> None:
        self._record("commitment")

    def on_acknowledgement(self, value: object, session: InboundSession) -> None:
        self._record("acknowledgement")

    def on_reveal(self, value: object, session: InboundSession) -> TurnOutcome:
        """The frozen R17 legality seam: `False` means game-illegal and nothing else."""
        self._record("reveal")
        return getattr(value, "hint", "") != ILLEGAL_HINT

    def on_final_nonce_reveal(self, value: object, session: InboundSession) -> None:
        self._record("final_nonce_reveal")

    def on_audit_disclosure(self, value: object, session: InboundSession) -> None:
        self._record("audit_disclosure")

    def on_result_agreement(
        self, agreement: ResultAgreement, session: InboundSession
    ) -> Sha256Digest:
        """Delegate to production; the digest is `ResultExchange`'s, never ours."""
        try:
            return self.exchange.accept_peer_request(agreement, GROUP_B)
        finally:
            self._record("result_agreement")
