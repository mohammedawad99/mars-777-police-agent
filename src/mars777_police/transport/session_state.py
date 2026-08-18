"""The authenticated peer identity, held in FastMCP's own session state.

Split out of `transport/server.py` when the KIT profile arrived: both tool
surfaces need the same session reader, and a surface importing the other's
module to get it would make the two registrations depend on each other for no
reason. Nothing here knows which profile is in force.

`Context.get_state`/`set_state` are session-scoped and persist across
`call_tool` on one Streamable-HTTP session, and `Context` never appears in a
published tool schema - so the wire contract is untouched and a caller cannot
supply its own identity. The write-back happens **after** the operation
returned: an operation that raises leaves the session exactly as
unauthenticated as it found it.
"""

from fastmcp import Context

from .inbound_session import InboundSession

AUTH_STATE_KEY = "mars777.authenticated_peer"
"""The one session-state key: an authenticated `group_id`, and nothing else."""


async def inbound(context: Context) -> InboundSession:
    """Read this session's bound identity, if Step-0 has established one."""
    bound = await context.get_state(AUTH_STATE_KEY)
    return InboundSession(context.session_id, bound if isinstance(bound, str) else None)


async def persist(context: Context, session: InboundSession) -> None:
    """Write back a binding the operation just proved. Failures never reach here."""
    if session.pending is not None:
        await context.set_state(AUTH_STATE_KEY, session.pending)
