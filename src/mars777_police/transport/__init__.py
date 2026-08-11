"""The FastMCP peer transport adapter.

An **adapter**, never a second implementation of the protocol. Everything here
validates wire shapes, converts them to and from the already-frozen semantic
values, and hands them to the Stage-4E-R16 application runtime, which remains the
sole authority on Step-0 policy, negotiation cadence, lock gating, turn legality
and the result cadence.

The layering that makes that true: `app` may not import `protocol`, and nothing
outside this package may import `fastmcp` or `pydantic`. Wire types stop here.
"""
