"""Which runtime is current, for the two adapters that both need to know.

Three of this agent's owners are lifecycle-scoped and one arrives late.
`TurnProtocolRuntime` is consumed after one turn, `OutboundEvidenceRuntime` and
`AuditRuntime` belong to one sub-game, and `ResultExchange` cannot exist at all
until the series has been played - it is assembled *from* six completed
sub-games. The inbound adapter and the outbound runner must nevertheless agree
on which of each is current, and until now nothing in production said so.

**Four typed slots, not a registry.** Every field is a named semantic runtime;
there is no `get(name)`, no string key, no `dict[str, object]` and no way to put
something in that nobody declared. A container that could hold anything would
let one peer's runtime be handed to another peer's adapter, and the type checker
would never notice.

**Unbound is a refusal, not `None`.** Each accessor raises the existing stale
identity rather than returning something a caller has to check, so an operation
that arrives before its runtime exists fails at the boundary instead of deeper
in with an `AttributeError`.

**The result is bound once.** A second, different `ResultExchange` for one
series would mean two answers to what the series produced, so it is refused
rather than overwritten.
"""

from dataclasses import dataclass, field

from .audit_runtime import AuditRuntime
from .outbound_evidence_runtime import OutboundEvidenceRuntime
from .protocol_errors import LocalDefectError, StaleMessageError
from .result_exchange import ResultExchange
from .turn_protocol_runtime import TurnProtocolRuntime


@dataclass(slots=True)
class ActiveRuntimeContext:
    """The current turn, sub-game and series-final owners, for one agent."""

    turn: TurnProtocolRuntime | None = field(default=None)
    evidence: OutboundEvidenceRuntime | None = field(default=None)
    audit: AuditRuntime | None = field(default=None)
    result: ResultExchange | None = field(default=None)

    def bind_turn(self, turn: TurnProtocolRuntime) -> None:
        """Make *turn* current, replacing only the per-turn owner.

        When a sub-game is already bound the cursor must agree with it: a turn
        from another sub-game reaching the live runtimes would be a local
        composition defect, and `TurnCursor` already carries the sub-game, so
        nothing had to be added to check it.
        """
        active = self.evidence
        if active is not None and turn.cursor.sub_game != active.context.sub_game:
            raise LocalDefectError(
                f"turn names sub-game {turn.cursor.sub_game},"
                f" not the active {active.context.sub_game}",
            )
        self.turn = turn

    def current_turn(self) -> TurnProtocolRuntime:
        """The live turn runtime, or a refusal if none has been bound."""
        if self.turn is None:
            raise StaleMessageError("no turn is active")
        return self.turn

    def bind_sub_game(self, evidence: OutboundEvidenceRuntime, audit: AuditRuntime) -> None:
        """Make one sub-game's producer and verifier current, together.

        Both are replaced or neither is: a producer for `g02` beside a verifier
        for `g01` would disclose one sub-game's nonces while auditing another.
        """
        if evidence.context.sub_game != audit.context.sub_game:
            raise LocalDefectError(
                f"a sub-game needs one identity, got evidence"
                f" {evidence.context.sub_game} and audit {audit.context.sub_game}",
            )
        self.evidence = evidence
        self.audit = audit

    def current_evidence(self) -> OutboundEvidenceRuntime:
        """The live evidence producer, or a refusal if no sub-game is bound."""
        if self.evidence is None:
            raise StaleMessageError("no sub-game is active")
        return self.evidence

    def current_audit(self) -> AuditRuntime:
        """The live audit runtime, or a refusal if no sub-game is bound."""
        if self.audit is None:
            raise StaleMessageError("no sub-game is active")
        return self.audit

    def bind_result(self, result: ResultExchange) -> None:
        """Adopt the series-final result owner. Once, for the whole series."""
        if self.result is not None:
            raise LocalDefectError("this series already has a result exchange")
        self.result = result

    def current_result(self) -> ResultExchange:
        """The result owner, or a refusal while the series is still running."""
        if self.result is None:
            raise StaleMessageError("the series result is not available yet")
        return self.result
