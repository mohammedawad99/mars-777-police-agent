"""The exact rendering two peers must both produce for one agreed scent model.

A semantic value rather than a naked byte string, for the same reason
`Sha256Digest` and `AuthProof` are: a port returns meaning, never transport
material, and `API_BOUNDARIES.md` P2 is enforced by a guard that reads every
port signature. What this carries is opaque by design - nobody outside the
mapping that produced it should interpret it - and its only operation is the one
the agreement needs: equality.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScentModelRendering:
    """One model's deterministic rendering, compared and never inspected."""

    value: bytes

    def __post_init__(self) -> None:
        if type(self.value) is not bytes or not self.value:
            raise ValueError("a model rendering is non-empty encoded content")

    @property
    def length(self) -> int:
        """How long the rendering is - the one property tests assert on."""
        return len(self.value)
