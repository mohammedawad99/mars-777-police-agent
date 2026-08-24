"""Who a `result_agreement` is authenticated as, on a session that proves nothing.

`RESULT_CONTRACT.md` R13-R1-8 requires **the authenticated sender identity**.
That property is source-required. Holding it in one Streamable-HTTP session was
this project's own choice, and a peer whose client opens a session per call -
POST, GET, POST, DELETE, which is what the reference clients do - satisfies the
property and fails the choice. It completes one authenticated Step-0 and is then
unrecognisable, so a result both sides genuinely agreed becomes unreachable for
a reason no source asked for.

**A stored Step-0 authenticates the series, never the next caller.** Trusting a
merged declaration alone would let anyone who knows the game identity submit a
contribution under the opponent's name. So a session that proves nothing must
carry its own proof: the request is authenticated on its own bytes, in its own
context, before anything in it is believed.

**Order is the whole design.** The proof is checked over the raw payload exactly
as it arrived - before semantic normalisation, because normalising first would
verify bytes the sender never sent. Only then is the sender resolved, and it is
resolved from the *verified Step-0 binding*, never from `contribution.group_id`:
letting the payload name its own author turns the downstream ownership check
into `x != x`.

**Fail-closed at every step**, and each refusal names which one: no proof, a
proof over other bytes, a key or profile we did not provision, no established
series, or a series that does not name us. Everything after this - game identity,
contribution ownership, six real entries, matching digests - is unchanged and
still has to pass.
"""

from collections.abc import Mapping
from typing import Protocol

from .auth_values import AuthProof
from .declaration_values import Declaration
from .participant_slots import PARTICIPANT_SLOTS
from .protocol_errors import AuthFailureError


class RequestAuthPort(Protocol):
    """Keyed verification of one request's own bytes, in its own context.

    Declared beside its only consumer rather than in `ports.py`: that module is
    the Stage-4E-R16 runtime port set and no runtime depends on this one.
    """

    def verify_request(self, payload: object, proof: AuthProof) -> bool:
        """Whether *proof* verifies over *payload* in the request context."""
        ...


def raw_payload(message: object) -> object:
    """The `payload` object exactly as it arrived, or a refusal.

    The proof covers the bytes the sender actually sent. Verifying a normalised
    projection instead would authenticate a document nobody transmitted, and any
    coercion our decoder performs - a default filled, a number retyped - would
    silently change what was checked.
    """
    if not isinstance(message, Mapping) or "payload" not in message:
        raise AuthFailureError("a result agreement carries its proof over its own payload")
    return message["payload"]


def opponent_of(declaration: Declaration | None, ours: str) -> str:
    """The other participant of an established series, or a typed refusal."""
    if not ours:
        raise AuthFailureError(
            "this group has no configured identity, so it cannot say which"
            " participant of a series is the opponent",
        )
    if declaration is None or not declaration.teams.is_merged:
        raise AuthFailureError(
            "no authenticated Step-0 has established this series, so there is no"
            " identity a result agreement could be authenticated as",
        )
    named = [
        str(team.group_id)
        for slot in PARTICIPANT_SLOTS
        if (team := getattr(declaration.teams, slot)) is not None
    ]
    # Requiring *us* by name first is the point: "whichever participant is not
    # us" answers a series between two other groups with one of them, which
    # would authenticate a stranger against a declaration we merely hold.
    if ours not in named:
        raise AuthFailureError(f"the established series does not name {ours!r} as a participant")
    others = [group for group in named if group != ours]
    if len(others) != 1:
        raise AuthFailureError(f"the established series names no single opponent of {ours!r}")
    return others[0]


def authenticated_sender(
    peer: str | None,
    payload: object,
    proof: AuthProof | None,
    declaration: Declaration | None,
    ours: str,
    authenticator: RequestAuthPort,
) -> str:
    """Return the identity this request is authenticated as, or refuse it.

    *peer* is the binding a Step-0 on this same session established, and wins
    unchanged where it exists - the stricter evidence is never downgraded.
    Otherwise *proof* must verify over *payload* before *declaration* is read.
    """
    if peer is not None:
        return peer
    if proof is None:
        raise AuthFailureError(
            "this session completed no Step-0, so a result agreement must carry its"
            " own keyed proof; none was sent",
        )
    if not authenticator.verify_request(payload, proof):
        raise AuthFailureError(
            "the result agreement's keyed proof does not verify over the request it"
            " arrived with, under the provisioned profile and key",
        )
    return opponent_of(declaration, ours)
