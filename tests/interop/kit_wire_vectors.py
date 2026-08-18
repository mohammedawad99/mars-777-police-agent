"""The pinned KIT **transport** vector material, copied for deterministic regression.

Source repository : https://github.com/Imreec/copthief-league-protocol
Pinned commit     : ad6557626587e09146af4283a5e808e7001343c5
Licence           : MIT, (c) 2026 Team ImreEyal (Imree Cohen, Eyal Shtinmetz)
                    and kit contributors.

`kit_vectors` pins the kit's *constructions*; this file pins the kit's **wire**:
the four tool names, the argument-name asymmetry, and the exact accept/refuse
rows of `vectors/turn_message.json` at that SHA. Only the expected values are
copied - every computed value lives in the tests beside this file, because an
oracle sharing the implementation under test proves nothing.

The wire is **PROMOTED de-facto interoperability guidance, not book law**. The
course book remains supreme; nothing here may relax a binding rule.
"""

from typing import Final

TOOLS: Final = ("negotiate", "receive_turn", "submit_audit", "receive_control")
"""The four public tool names, in the kit's own order (`transport/client.py`)."""

ARGUMENT_NAMES: Final = {
    "negotiate": "message",
    "receive_turn": "message",
    "submit_audit": "payload",
    "receive_control": "message",
}
"""The asymmetry, and it is load-bearing: `submit_audit` alone takes `payload`."""

TURN_REQUIRED: Final = ("step", "sender", "hint", "smell_grid", "commit", "timestamp")
TURN_OPTIONAL: Final = ("barrier_placed", "capture_claim", "claim_response", "win_claim")
AUDIT_REQUIRED: Final = ("sender", "records", "result_claim")
CONTROL_REQUIRED: Final = ("kind", "sender")
CONTROL_OPTIONAL: Final = ("sub_game_number", "status", "step_budget", "payload")

COMMIT: Final = "a" * 64

TURN: Final = {
    "step": 7,
    "sender": "police",
    "hint": "north of the park",
    "smell_grid": {"3,3": 0.9, "3,4": 0.5, "4,3": 0.5},
    "commit": COMMIT,
    "timestamp": "2026-08-08T19:00:00Z",
    "barrier_placed": [5, 6],
    "capture_claim": None,
    "claim_response": None,
    "win_claim": None,
}
"""`vectors/turn_message.json` row 1: the full ten-key set, nulls explicit, ACCEPT."""


class _Absent:
    """The one sentinel meaning "delete this key" - never "send null"."""


ABSENT: Final = _Absent()


def turn(**changes: object) -> dict[str, object]:
    """The accepted turn with *changes* applied; `ABSENT` deletes the key."""
    message: dict[str, object] = dict(TURN)
    for name, value in changes.items():
        if value is ABSENT:
            del message[name]
        else:
            message[name] = value
    return message


TURN_REFUSALS: Final = (
    ({"timestamp": ""}, "timestamp: required non-empty str"),
    ({"commit": ABSENT}, "commit: required 64-char lowercase hex"),
    ({"commit": COMMIT.upper()}, "commit: required 64-char lowercase hex"),
    ({"smell_grid": {"3,3": "0.9"}}, "smell_grid: required dict of 'r,c' -> number"),
    ({"step": -1}, "step: required non-negative int"),
)
"""Rows 3-7 of the pinned file: every one REFUSED, and why the kit refuses it."""

TURN_TOLERATED: Final = {"unknown_field": {"anything": 1}}
"""Row 2: an unknown key is tolerated and ignored - the kit's extension seam."""

AUDIT: Final = {
    "sender": "police",
    "records": [
        {"payload": {"step": 1, "move": "MOVE:N"}, "nonce": "0" * 32, "commit": COMMIT},
    ],
    "result_claim": "capture",
}
"""`AuditPayload` (`proto/messages.py`), records in the kit's own record shape."""

RESULT_CLAIMS: Final = ("capture", "survival", "timeout", "technical_loss", "tamper_forfeit")
"""`rules/outcome.Outcome` - what `send_audit(outcome.value)` can actually carry."""

CONTROL: Final = {
    "kind": "status",
    "sender": "police",
    "sub_game_number": 1,
    "status": "ready",
    "step_budget": 0.0,
    "payload": None,
}
CONTROL_KINDS: Final = ("enable", "status", "restart", "quit")
"""`ControlMessage.kind` - the complete pinned vocabulary, and nothing beside it."""

NEGOTIATION: Final = {
    "terms": {"grid_size": 10, "max_steps": 35},
    "nonce": "a1a2a3a4b1b2b3b4c1c2c3c4d1d2d3d4",
    "signature": "b" * 64,
    "group_id": "team-aleph",
    "role": "police",
    "sub_game_number": 1,
    "identity": {"group_id": "team-aleph", "group_name": "Aleph", "llm_model": "template"},
    "game_uid": "1e73c318-5b29-4a7b-1c60-ecb8286265f0",
}
"""`Negotiation.to_wire()` omits every `None`, so an absent optional is silence."""

NEGOTIATION_REQUIRED: Final = ("terms", "nonce", "signature", "group_id")
NEGOTIATION_OPTIONAL: Final = (
    "role",
    "sub_game_number",
    "identity",
    "scent_model_sha256",
    "wire_shape_sha256",
    "info_mode_sha256",
    "smell_binding_sha256",
    "info_mode",
    "game_uid",
)


_OBJECT: Final = {"additionalProperties": True, "type": "object"}
PINNED_SCHEMAS: Final = {
    name: {"properties": {argument: _OBJECT}, "required": [argument], "type": "object"}
    for name, argument in ARGUMENT_NAMES.items()
}
"""The pinned peer's OWN published `tools/list` schemas, dumped from `ad65576`.

Read out of a running pinned server on its own FastMCP major (2.14.7) rather
than transcribed from its source, because what a stranger reads is what the
framework published and not what the handler was annotated with.
"""
