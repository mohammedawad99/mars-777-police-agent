"""Which side this repository is, as one constant nothing may override.

The role is a property of the **package**, not of a command line or an
environment variable: `infra.settings` checks the operator's value against this
and refuses a disagreement rather than obeying it. Keeping it here, below both
the facade and the composition modules, means every one of them agrees by
construction instead of by convention.
"""

from typing import Final

from .app.sealed_record_values import ActorRole

ROLE: Final[ActorRole] = ActorRole.POLICE
"""This repository's fixed competitive role."""
