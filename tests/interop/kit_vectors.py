"""Minimal pinned KIT CORE vector material, copied for deterministic regression.

Source repository : https://github.com/Imreec/copthief-league-protocol
Pinned commit     : ad6557626587e09146af4283a5e808e7001343c5
Licence           : MIT, (c) 2026 Team ImreEyal (Imree Cohen, Eyal Shtinmetz)
                    and kit contributors.

Only the data required to pin our own conformance is reproduced - no kit
algorithm is copied, because an oracle that shares the implementation under
test proves nothing. Every expected value below is the kit's, and every
computed value in the tests beside this file is ours.

The kit is **interoperability guidance, not project source**: the course book
remains supreme, and where the two disagree on a binding rule the book wins
(see the pheromone family conflict recorded in the scent tests).
"""

from typing import Final

CANONICAL: Final = (
    ({"b": 1, "a": {"d": 4, "c": 3}}, '{"a":{"c":3,"d":4},"b":1}'),
    ({"hint": "אני ליד הכיכר", "move": "MOVE:N"}, '{"hint":"אני ליד הכיכר","move":"MOVE:N"}'),
    ({"emoji": "🙂", "x": 1}, '{"emoji":"🙂","x":1}'),
    ({"a": True, "b": None, "c": [1, 2, 3]}, '{"a":true,"b":null,"c":[1,2,3]}'),
    # The FULLWIDTH TILDE below is the point - it is the code-point sort trap, and
    # replacing it with an ASCII tilde would delete what this row tests.
    (
        {"～": "high-BMP key", "🙂": "astral key"},  # noqa: RUF001
        '{"～":"high-BMP key","🙂":"astral key"}',  # noqa: RUF001
    ),
)
"""`(object, expected canonical text)` - compact separators, sorted, non-ASCII native.

The last row is the key-sort trap: sorting is by Unicode **code point**, so
U+FF5E precedes U+1F642. A UTF-16 code-unit sort reverses them.
"""

FLOATS: Final = (
    (
        {
            "decay_per_step": 0.1,
            "emit_intensity": 0.9,
            "min_center_intensity": 0.5,
            "ram_gb": 31.8,
            "vram_gb": 6.0,
        },
        '{"decay_per_step":0.1,"emit_intensity":0.9,"min_center_intensity":0.5,'
        '"ram_gb":31.8,"vram_gb":6.0}',
    ),
    ({"tiny": 1e-07, "huge": 1e16}, '{"huge":1e+16,"tiny":1e-07}'),
)
"""Binary floats, rendered by Python's shortest round-trip repr - exponent forms included."""

COMMITMENTS: Final = (
    (
        {
            "step": 0,
            "type": "system_spec",
            "spec": {"os": "Linux", "cpu_cores": 4, "ram_gb": 16.0, "vram_gb": 0.0},
            "model": "cli-default",
            "code_version": "1.0",
            "group_name": "Example-Team",
            "sub_game_number": 1,
        },
        "0f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "69c9a786d18829990291cd0ffb768eacfa009011b0c89a6f4f32330551e2003e",
    ),
    (
        {
            "step": 1,
            "state": "grid=7x7;self=[4, 3];barriers=[]",
            "position": [4, 3],
            "move": "MOVE:S",
            "intent": "truth",
            "hint": "I keep to the main avenues.",
        },
        "112233445566778899aabbccddeeff00",
        "aa6420e2d3a907d6c140856caecbb351b4d5ad98e381549c28268669af378dcc",
    ),
    (
        {
            "step": 2,
            "state": "grid=7x7;self=[2, 4];barriers=[[1, 1]]",
            "position": [2, 4],
            "move": "MOVE:N",
            "intent": "lie",
            "hint": "אני ליד הכיכר 🙂",
        },
        "deadbeefcafef00dfeedface00c0ffee",
        "2caaeb0a7e656868b85166a9ebe34226bae4fdcb79cb7a0a23759121769d9338",
    ),
)
"""`(payload, nonce, expected commit)` - `SHA256(canonical(payload)|nonce)`, nonce OUTSIDE."""

NONCE_INSIDE: Final = "833e47c675448a9072660b984d8514a5786792372f415caea1b0d4348b301875"
"""The same record hashed with the nonce *inside* - the kit's `book_ch5_listing_form`.

Pinned so the two constructions can be proved distinct rather than assumed to be.
"""


TERMS: Final = {
    "board_size": 7,
    "smell_grid_size": 5,
    "decay_per_step": 0.1,
    "emit_intensity": 0.9,
    "min_center_intensity": 0.5,
    "max_steps": 35,
    "barriers_max": 14,
    "setting": "Haifa",
    "hint_max_words": 15,
    "axis_origin_corner": "top-left",
    "axis_start_index": 0,
    "thief_start": [3, 3],
    "cop_start": [0, 0],
    "num_games": 1,
}
"""The flat agreed terms both peers hash - the kit's `terms_from_config` subset."""

GAME_UID: Final = "1e73c318-5b29-4a7b-1c60-ecb8286265f0"
GAME_ID: Final = "team-aleph-vs-team-bet"
GROUPS: Final = ("team-aleph", "team-bet")

TERMS_NONCE: Final = "a1a2a3a4b1b2b3b4c1c2c3c4d1d2d3d4"
TERMS_SIGNATURE: Final = "80793141f22b6193b02a74d5955767ad1e24abbac172894358ec13622b85a04c"

CONSENSUS: Final = (
    (
        {
            "קבוצה_א": "team-aleph",
            "קבוצה_ב": "team-bet",
            "תוצאה": {"מנצחת": "team-aleph", "ניקוד": [20, 5]},
            "game_uid": "f757f50d-d4f4-17e7-06cf-755905739b16",
            "tokens_total_series": 0,
            "github_commit": "abc1234",
        },
        "af661c4101cfe73470794102ab7417b67ef0ea5b8c3bc55b38133ac5f8e95049",
    ),
    (
        {
            "סדרה": [{"משחקון": 1, "ניקוד": [5, 10]}, {"משחקון": 2, "ניקוד": [20, 5]}],
            "ram_gb": 31.8,
            "decay_per_step": 0.1,
            "mutual_agreement": True,
        },
        "77c4cce023b641406db0dd3efd7ca44563aa8e4b8eaa9e02c128fa9b9ef7bbd7",
    ),
)
"""`(report, expected consensus signature)` - the SPACED canonical form, sign-then-insert."""
