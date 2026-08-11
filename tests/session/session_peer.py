"""One production peer in its own process: real server, real adapter, real owners.

Nothing behind this server is a double. The nine inbound operations reach
`InboundPeerOperations`, which reaches `PregameSessionRuntime`, the turn and
audit runtimes and `ResultExchange` - so a refusal observed over HTTP came from
the application, and a binding observed over HTTP came from a real Step-0 keyed
verification.

The turn provider hands out one runtime **per operation**, each prepared for the
phase that operation legitimately arrives in. That is the lifecycle design R3
settled: providers are the caller's, and the adapter resolves one per call.
"""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
for _name in ("transport", "turn", "audit", "protocol"):
    sys.path.insert(0, str(TESTS / _name))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def turn_sequence() -> object:
    """Fresh, ack-ready and reveal-ready runtimes, in inbound call order."""
    import turn_builders

    ready = turn_builders.runtime()
    ready.register_local_commitment(turn_builders.commitment(digest=turn_builders.OUR_DIGEST))
    prepared = iter(
        [turn_builders.runtime(), ready, turn_builders.advanced(turn_builders.runtime())]
    )
    last = turn_builders.runtime()

    def resolve() -> object:
        nonlocal last
        last = next(prepared, last)
        return last

    return resolve


def main(port: int) -> None:
    """Serve one production peer until terminated."""
    import audit_builders
    import session_builders as build
    import uvicorn

    from mars777_police.transport.peer_operations import InboundPeerOperations
    from mars777_police.transport.server import build_server

    pregame = build.pregame()
    pregame.adopt_config(build.agreed())
    audit = audit_builders.runtime()
    operations = InboundPeerOperations(pregame, turn_sequence(), lambda: audit, build.exchange())
    application = build_server(operations, name="r3r-peer").http_app(path="/mcp")
    uvicorn.run(application, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main(int(sys.argv[1]))
