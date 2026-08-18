"""Which wire a process speaks, decided once and read everywhere.

One authority for both directions: it selects the tool schemas the ingress
registers **and** the argument shape the outbound client sends. A process whose
server spoke one wire and whose client spoke the other would be interoperable
with nobody, and the fault would look like an opponent problem from both sides.

**Selected before construction, never after.** A transport profile cannot be
negotiated by the very messages whose encoding it governs, and probing - try one
shape, fall back to the other - turns an integrity failure into a silent
downgrade. `ExternalMode` is the operator's out-of-band choice; this is the wire
consequence of it, and the mapping is total so no mode can be forgotten.
"""

from enum import StrEnum

from ..app.kit_preset import ExternalMode


class TransportEnvelopeProfile(StrEnum):
    """The two envelope families this build can register and send."""

    STRICT_PROJECT = "STRICT_PROJECT"
    """Our own `request = {kind, payload}` envelope, with nine closed kinds."""

    KIT_EXTERNAL = "KIT_EXTERNAL"
    """The pinned kit's `message`/`payload` objects (`ad65576`, reference-v3)."""


_BY_MODE = {
    ExternalMode.STRICT_INTERNAL: TransportEnvelopeProfile.STRICT_PROJECT,
    ExternalMode.KIT_CORE_V1: TransportEnvelopeProfile.KIT_EXTERNAL,
}
"""Total by construction: a new mode without a wire fails at import, not in play."""


def transport_profile(mode: ExternalMode) -> TransportEnvelopeProfile:
    """The envelope family *mode* selects for a whole process lifetime."""
    return _BY_MODE[mode]
