"""Base error type and shared validation helper for the game domain.

The domain reports *legality* as a verdict (``is_legal_move`` /
``legal_moves``) and never raises for it, per PRD-01 §17. These errors cover
malformed inputs and caller defects only -- the outer layers map them onto the
locked ``E-LOCAL-VALIDATION`` / ``E-LOCAL-DEFECT`` codes in
``docs/architecture/ERROR_MODEL.md``. Messages carry local diagnostics only:
never a key, nonce, secret, or any opponent state.
"""


class DomainError(Exception):
    """Base class for every deterministic game-domain failure."""


def require_int(value: object, name: str, error: type[DomainError]) -> int:
    """Return *value* when it is a real ``int``, otherwise raise *error*.

    ``bool`` is rejected explicitly: it is an ``int`` subclass, and silently
    accepting ``True`` as ``1`` would be exactly the coercion PRD-01 forbids.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise error(f"{name} must be an int, got {type(value).__name__}")
    return value
