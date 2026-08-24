"""`receive_control` on the KIT wire: the pinned status signal, and the result.

The pinned kit uses this tool for a status signal with a closed four-word
vocabulary. This project's own frozen matrix has always paired the same tool
with exactly one semantic kind — `result_agreement` — and Stage 9C makes that one
kind reachable externally so an alternating counted series can complete the
agreement its result depends on.

Two properties matter more than the feature: a peer sending the **old** form must
be answered exactly as before, and anything else at all must fail closed without
touching result state. Both are pinned here.
"""

import asyncio
from typing import Any

import pytest
from fastmcp import Client
from kit_session_support import kit_context, kit_server
from kit_wire_vectors import ARGUMENT_NAMES, TOOLS
from peer_recorder import RecordingOperations

from mars777_police.app.protocol_errors import AuthFailureError, MalformedMessageError
from mars777_police.app.result_values import InvalidResultValueError
from mars777_police.transport.codec_final import decode_result_agreement
from mars777_police.transport.inbound_session import InboundSession
from mars777_police.transport.kit_control_envelope import (
    KitResultAgreementMessage,
    parse_kit_control,
)
from mars777_police.transport.kit_envelopes import KitControlMessage

LEGACY: dict[str, Any] = {
    "kind": "status",
    "sender": "police",
    "sub_game_number": 1,
    "status": "ready",
}

CONTRIBUTION: dict[str, Any] = {
    "group_id": "MaRs-777",
    "entries": [{"sub_game": n, "github_commit": "a" * 40, "tokens": 100 + n} for n in range(1, 7)],
}

AGREEMENT: dict[str, Any] = {
    "kind": "result_agreement",
    "payload": {
        "game_id": "MaRs-777-vs-s82kma9e",
        "game_uid": "43994252-2e4d-2b5c-9baa-4bf7aef5b5d6",
        "declaration_ref": "declaration_MaRs-777-vs-s82kma9e.json",
        "timestamp": "2026-08-24T12:00:00Z",
        "contribution": CONTRIBUTION,
    },
}


def served() -> dict[str, dict[str, object]]:
    """The tool schemas exactly as a peer's `tools/list` receives them."""

    async def run() -> dict[str, dict[str, object]]:
        async with Client(kit_server(RecordingOperations(), kit_context())) as client:
            return {tool.name: tool.inputSchema for tool in await client.list_tools()}

    return asyncio.run(run())


def test_the_public_surface_is_still_exactly_the_four_pinned_tools() -> None:
    """No fifth tool. The extension reuses the one `receive_control` already had."""
    assert sorted(served()) == sorted(TOOLS)


def test_receive_control_still_publishes_exactly_its_pinned_argument() -> None:
    """The injected session is not part of the schema a stranger reads."""
    schema = served()["receive_control"]

    assert list(schema["properties"]) == [ARGUMENT_NAMES["receive_control"]]
    assert schema["required"] == [ARGUMENT_NAMES["receive_control"]]


def test_the_legacy_status_form_is_unchanged() -> None:
    """A peer on the pinned vocabulary parses to the pinned model, as before."""
    parsed = parse_kit_control(LEGACY)

    assert isinstance(parsed, KitControlMessage)
    assert parsed.kind == "status"


@pytest.mark.parametrize("word", ["enable", "status", "restart", "quit"])
def test_every_pinned_control_word_still_parses_as_the_legacy_form(word: str) -> None:
    assert isinstance(parse_kit_control({**LEGACY, "kind": word}), KitControlMessage)


def test_the_result_agreement_form_carries_the_existing_wire_model() -> None:
    """The sender's own six-entry contribution travels with it, unchanged."""
    parsed = parse_kit_control(AGREEMENT)

    assert isinstance(parsed, KitResultAgreementMessage)
    assert len(parsed.payload.contribution.entries) == 6
    decoded = decode_result_agreement(parsed.payload)
    assert decoded.contribution.group_id == "MaRs-777"
    assert [entry.tokens for entry in decoded.contribution.entries] == [
        101,
        102,
        103,
        104,
        105,
        106,
    ]


@pytest.mark.parametrize(
    ("name", "body"),
    [
        ("an unknown control word", {"kind": "settle", "sender": "police"}),
        ("no discriminator at all", {"sender": "police", "status": "x"}),
        ("a result agreement with no payload", {"kind": "result_agreement"}),
        ("a result agreement with a partial payload", {"kind": "result_agreement", "payload": {}}),
        ("a payload that is not an object", {"kind": "result_agreement", "payload": 7}),
    ],
)
def test_any_other_control_form_fails_closed(name: str, body: dict[str, Any]) -> None:
    """Refused before anything is read, so nothing can be mutated by it."""
    with pytest.raises(MalformedMessageError):
        parse_kit_control(body)


def test_the_grammar_is_not_broadened_beyond_the_two_accepted_forms() -> None:
    """Exactly two members: the pinned status message and the one semantic kind."""
    accepted = {"enable", "status", "restart", "quit", "result_agreement"}
    for word in accepted:
        body = AGREEMENT if word == "result_agreement" else {**LEGACY, "kind": word}
        assert parse_kit_control(body) is not None
    for refused in ("step0", "commitment", "reveal", "audit_disclosure", "config_lock"):
        with pytest.raises(MalformedMessageError):
            parse_kit_control({**LEGACY, "kind": refused})


def test_a_short_contribution_is_refused_before_it_becomes_a_value() -> None:
    """Five entries are not six, and they are never padded or repaired."""
    short = {
        **AGREEMENT,
        "payload": {
            **AGREEMENT["payload"],
            "contribution": {"group_id": "MaRs-777", "entries": CONTRIBUTION["entries"][:5]},
        },
    }
    parsed = parse_kit_control(short)
    with pytest.raises(InvalidResultValueError):
        decode_result_agreement(parsed.payload)  # type: ignore[union-attr]


def test_an_unauthenticated_session_can_never_reach_result_state() -> None:
    """`require_peer` refuses before any runtime is consulted, on either wire."""
    unbound = InboundSession("session-1", None)

    assert unbound.is_authenticated is False
    with pytest.raises(AuthFailureError):
        unbound.require_peer()
