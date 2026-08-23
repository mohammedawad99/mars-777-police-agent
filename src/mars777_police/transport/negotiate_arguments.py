"""Which of the three agreed `negotiate` spellings arrived, decided by shape.

The pairing froze `{"tool":"negotiate","kind":"step0"}` and never said whether
`kind` and `payload` were top-level MCP arguments or nested inside a `request`
object. Both teams implemented to the letter and to different shapes, and a
rehearsal Step-0 was rejected at input validation *before* authentication - no
HMAC checked, no sub-game started, no artifact written. Neither reading was
wrong, so the resolution is to accept both rather than to argue which letter won.

Three shapes, one meaning each:

    message={...}                              a per-sub-game KIT greeting
    kind="step0", payload={...}                the agreed cross-team Step-0
    request={"kind":"step0","payload":{...}}   the same, in our native envelope

**Dispatch is on shape, never on a caller-supplied selector.** A caller that
could name the route could name the wrong one, and a receiver has no way to tell
a mistake from a downgrade attempt.

**Only `step0` is accepted here.** The other internal kinds - `config_proposal`,
`config_lock` - are not part of what the pairing exposed on the public route, and
a kind this function does not know is refused rather than forwarded.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from ..app.protocol_errors import MalformedMessageError

Step0Handler = Callable[[dict[str, Any]], Awaitable[None]]
"""Receives one Step-0 exchange payload, already unwrapped from its envelope."""

STEP0 = "step0"


def step0_arguments(
    message: dict[str, Any] | None,
    request: dict[str, Any] | None,
    kind: str | None,
    payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """The Step-0 payload if this call is one, or `None` if it is a greeting.

    Refuses a call that mixes spellings or names a kind this route does not
    carry, rather than guessing which half the caller meant.
    """
    if request is not None:
        if kind is not None or payload is not None:
            raise MalformedMessageError(
                "negotiate carried both a request envelope and top-level kind/payload;"
                " one call states one shape",
            )
        return _from_request(request)
    if kind is None and payload is None:
        return None
    if kind is None or payload is None:
        raise MalformedMessageError(
            "negotiate needs kind and payload together; one without the other names nothing",
        )
    _require_step0(kind)
    return payload


def _from_request(request: dict[str, Any]) -> dict[str, Any]:
    """Unwrap our native `{kind, payload}` envelope, or refuse its shape."""
    inner_kind, inner_payload = request.get("kind"), request.get("payload")
    if not isinstance(inner_kind, str) or not isinstance(inner_payload, dict):
        raise MalformedMessageError(
            "a negotiate request envelope carries a string kind and an object payload",
        )
    _require_step0(inner_kind)
    return inner_payload


def _require_step0(kind: str) -> None:
    """Refuse any kind but the one this public route agreed to carry."""
    if kind != STEP0:
        raise MalformedMessageError(
            f"the public negotiate route carries {STEP0!r} only; {kind!r} is not exposed here",
        )
