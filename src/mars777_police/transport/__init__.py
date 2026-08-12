"""The FastMCP peer transport adapter.

An **adapter**, never a second implementation of the protocol. Everything here
validates wire shapes, converts them to and from the already-frozen semantic
values, and hands them to the Stage-4E-R16 application runtime, which remains the
sole authority on Step-0 policy, negotiation cadence, lock gating, turn legality
and the result cadence.

The layering that makes that true: `app` may not import `protocol`, and nothing
*inward* of this package may import `fastmcp` or `pydantic` - `app`, `domain`,
`protocol` and `infra` all stay testable and portable without the framework.
Wire types stop here. The Stage-5-R5 composition root sits **outside** transport
and names `FastMCP` for exactly one thing: the type of the server it assembles.
"""
