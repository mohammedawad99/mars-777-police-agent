"""Protocol adapters: canonical bytes and the commitment computed over them.

A package marker, deliberately not a façade. Callers import the exact module they
need — `protocol.canonical` for bytes, `protocol.commitment` for the sealed
record and its digest — so nothing here re-exports, registers or dynamically
discovers anything. Stage 4E-R9-RESUME opened this package with those two
modules; the remaining rows of `MODULE_BOUNDARIES.md` (`keyed_auth`,
`config_lock`, `messages`, `declaration`, `profiles`) are not implemented.
"""
