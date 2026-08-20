"""Turning a persisted log's action back into the domain value it was.

The log writes an action through the same two-key tagged shape the wire uses, so
reading one back is a wire concern and belongs here beside `decode_action`
rather than in a viewer. Nothing else about a log is decoded here.
"""

from collections.abc import Mapping

from pydantic import TypeAdapter, ValidationError

from ..app.protocol_errors import MalformedMessageError
from ..domain.actions import PhysicalAction
from .codec_turn import decode_action
from .wire_turn import ActionWire

ACTIONS: TypeAdapter[ActionWire] = TypeAdapter(ActionWire)


def replay_action(raw: Mapping[str, object] | object) -> PhysicalAction:
    """Return the action a log entry recorded, refusing any other shape."""
    try:
        return decode_action(ACTIONS.validate_python(raw))
    except ValidationError as failure:
        raise MalformedMessageError(f"a logged action is not an action: {raw!r}") from failure
