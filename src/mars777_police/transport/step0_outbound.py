"""Sending **our** half of the mutual Step-0, in the agreed cross-team envelope.

Step-0 is an exchange, not a submission: each side sends its own authenticated
declaration and each verifies the other's. Accepting the peer's and stopping
there leaves them waiting on a reciprocal that never arrives, which is exactly
what a live rehearsal measured - their runner accepted our `200 OK`, entered its
inbound wait, and timed out after 30s having received nothing.

**The envelope is the agreed top-level one**, not this project's native
`{"request": {...}}`. The pairing froze
`negotiate(kind="step0", payload=<Step0DeclarationExchange>)` as the cross-team
form; our own receiver accepts both, but theirs is entitled to accept only what
was agreed, so what we *send* uses the agreed spelling.

A dedicated client rather than the internal `PeerClient`: that one builds
arguments through `strict_arguments`, which can only produce the native
envelope. Teaching it a second shape would let any internal call site send the
wrong one.
"""

from typing import Any

from fastmcp import Client

from ..app.peer_pregame_messages import Step0DeclarationExchange
from .call_arguments import wire_json
from .codec_declaration import encode_step0


async def send_step0(opponent: str, exchange: Step0DeclarationExchange) -> None:
    """Send our authenticated declaration to *opponent*, once."""
    payload: dict[str, Any] = wire_json(encode_step0(exchange))
    async with Client(opponent) as client:
        await client.call_tool("negotiate", {"kind": "step0", "payload": payload})
