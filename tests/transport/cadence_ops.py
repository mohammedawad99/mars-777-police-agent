"""A peer that runs the **production** result workflow, and reports its verdict.

Nothing about the result algorithm lives here. The process builds fixtures and
injects dependencies; `app.result_exchange.ResultExchange` owns the cadence, the
digest, the comparison and the completion verdict, so a defect in any of them
fails this harness instead of being masked by test-local arithmetic.
"""

import json
from pathlib import Path

from r16_builders import (
    COMMIT_A,
    COMMIT_B,
    CUMULATIVE,
    GAME_ID,
    GAME_UID,
    GROUP_A,
    GROUP_B,
    LINES,
    LINKS,
    PARTICIPANTS,
    FixedClock,
    merged,
)

from mars777_police.app.artifact_values import GitCommitSha
from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.result_agreement_runtime import ResultAgreementRuntime
from mars777_police.app.result_exchange import ResultExchange
from mars777_police.app.result_values import ResultContribution, ResultContributionEntry
from mars777_police.protocol.result_core import ResultDigester
from mars777_police.transport.inbound_session import InboundSession

COMMITS = {GROUP_A: COMMIT_A, GROUP_B: COMMIT_B}


def contribution_for(group_id: str, base: int) -> ResultContribution:
    """One participant's own six-entry contribution."""
    commit = COMMITS[group_id]
    return ResultContribution(
        group_id,
        tuple(ResultContributionEntry(i, commit, base + i) for i in range(1, 7)),
    )


def exchange_for(group_id: str, base: int) -> ResultExchange:
    """Build the production workflow for one peer, transport injected later."""
    return ResultExchange(
        ResultAgreementRuntime(group_id, GAME_ID, GAME_UID, PARTICIPANTS, FixedClock()),
        _Unsent(),
        ResultDigester(),
        merged(),
        LINES,
        LINKS,
        CUMULATIVE,
        contribution_for(group_id, base),
    )


class _Unsent:
    """A transport that refuses to send - a server-side peer never initiates."""

    async def send_result_agreement(self, agreement: ResultAgreement) -> Sha256Digest:
        raise AssertionError("this peer answers requests; it does not open one")


class CadenceOperations:
    """One peer's inbound handler, delegating to the production workflow."""

    def __init__(self, group_id: str, status: Path, base: int = 100) -> None:
        self.group_id = group_id
        self.peer = GROUP_A if group_id == GROUP_B else GROUP_B
        self.status = status
        self.exchange = exchange_for(group_id, base)
        if self.exchange.runtime.is_proposer:
            # The proposer chose the timestamp before its request left, so its
            # process starts holding it - that is what makes the echo check on
            # the second request meaningful rather than vacuous.
            self.exchange.timestamp = FixedClock().now()
            self.exchange.own_request_sent = True
        self._write()

    def _write(self) -> None:
        exchange = self.exchange
        self.status.write_text(
            json.dumps(
                {
                    "group_id": self.group_id,
                    "is_proposer": exchange.runtime.is_proposer,
                    "local_digest": exchange.local_digest.value if exchange.local_digest else None,
                    "peer_digest": exchange.peer_digest.value if exchange.peer_digest else None,
                    "own_request_sent": exchange.own_request_sent,
                    "peer_request_handled": exchange.peer_request_handled,
                    "verified": exchange.verified,
                    "is_agreed": exchange.is_agreed,
                    "timestamp": exchange.timestamp.value if exchange.timestamp else None,
                }
            ),
            encoding="utf-8",
        )

    def on_result_agreement(
        self, agreement: ResultAgreement, session: InboundSession
    ) -> Sha256Digest:
        """Delegate to production; the sender is this fixture's declared opponent.

        Not `agreement.contribution.group_id`: feeding that guard its own input
        makes it `x != x`. Production binds the real identity to the session -
        this harness exists to exercise the digest cadence, not authentication.
        """
        try:
            digest = self.exchange.accept_peer_request(agreement, self.peer)
        finally:
            self._write()
        return digest

    def on_step0(self, exchange: object, session: InboundSession) -> None: ...
    def on_config_proposal(self, value: object, session: InboundSession) -> None: ...
    def on_config_lock(self, value: object, session: InboundSession) -> None: ...
    def on_commitment(self, value: object, session: InboundSession) -> None: ...
    def on_acknowledgement(self, value: object, session: InboundSession) -> None: ...
    def on_reveal(self, value: object, session: InboundSession) -> bool:
        return True

    def on_final_nonce_reveal(self, value: object, session: InboundSession) -> None: ...
    def on_audit_disclosure(self, value: object, session: InboundSession) -> None: ...


__all__ = ["CadenceOperations", "GitCommitSha", "contribution_for", "exchange_for"]
