"""Shared fixtures for the two result-agreement authentication suites.

The synthetic key is published: these vectors are the ones the pairing exchanged,
and a vector nobody else can recompute proves nothing. `KEY` is the secret's own
UTF-8 bytes because that is what production does - it never hex-decodes, and two
vectors published on the opposite assumption were wrong.
"""

from mars777_police.app.auth_values import AuthProfile, AuthProof, KeyId
from mars777_police.app.declaration_values import Declaration
from mars777_police.protocol.declaration import RequestAuthenticator
from mars777_police.protocol.keyed_auth import (
    RESULT_CONTEXT,
    HmacSha256Provider,
    KeyedAuthenticator,
)

SECRET = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
KEY = SECRET.encode()
KEY_ID = "vector-key"
VECTOR = "dcd34564ec3b5d8910fed5a03aabf9ddb63d05346c08b726bf6b0dd172692335"
COMMIT = "9078407a770c9afc595d70ced968ad5e4e2189a9"


def keyed(key_id: str = KEY_ID, key: bytes = KEY) -> KeyedAuthenticator:
    """A provisioned authenticator over one profile and one key."""
    return KeyedAuthenticator(
        AuthProfile.HMAC_SHA256, KeyId(key_id), HmacSha256Provider({key_id: key})
    )


def authority(key_id: str = KEY_ID, key: bytes = KEY) -> RequestAuthenticator:
    """The request-context adapter over that authenticator."""
    return RequestAuthenticator(keyed(key_id, key))


def payload(group_id: str = "ahk-yosi", tokens: int = 1200) -> dict[str, object]:
    """One result-agreement request payload, in the shape the peer sends it."""
    return {
        "game_id": "MaRs-777-vs-ahk-yosi",
        "game_uid": "5ed16f3b-4e6b-4e9d-65bf-8f5abab699f2",
        "declaration_ref": "declaration_MaRs-777-vs-ahk-yosi.json",
        "timestamp": "2026-08-24T18:00:00Z",
        "contribution": {
            "group_id": group_id,
            "entries": [
                {"sub_game": 1, "github_commit": COMMIT, "tokens": tokens},
                {"sub_game": 2, "github_commit": COMMIT, "tokens": 1150},
                {"sub_game": 3, "github_commit": COMMIT, "tokens": 1050},
                {"sub_game": 4, "github_commit": COMMIT, "tokens": 1200},
                {"sub_game": 5, "github_commit": COMMIT, "tokens": 900},
                {"sub_game": 6, "github_commit": COMMIT, "tokens": 1300},
            ],
        },
    }


def proof_over(body: object, key_id: str = KEY_ID, key: bytes = KEY) -> AuthProof:
    """A request proof over *body*, in the result context."""
    return keyed(key_id, key).prove(RESULT_CONTEXT, body)


def sides(declaration: Declaration) -> tuple[str, str]:
    """Both participants, read from the declaration rather than guessed."""
    first, second = declaration.teams.group_a, declaration.teams.group_b
    assert first is not None and second is not None
    return first.group_id, second.group_id
