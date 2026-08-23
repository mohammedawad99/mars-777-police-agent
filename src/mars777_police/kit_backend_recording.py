"""The claim name each terminal outcome is disclosed under.

Kept out of `kit_backend` so the backend never imports the artifact writer, and
so the mapping has one home rather than being rebuilt beside each use.
"""

from .app.kit_messages import KitResultClaim
from .domain.terminal import Outcome

CLAIM = {one: KitResultClaim(one.value.lower()) for one in Outcome}
"""Each terminal outcome under the claim name the disclosure carries."""
