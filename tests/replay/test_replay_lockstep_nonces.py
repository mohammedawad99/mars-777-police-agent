"""Two commitments per step, two nonces per step, and no false accusation.

Every lockstep step carries both sides' commitments, and `final_reveal` labels
each released nonce with the role it belongs to. A nonce map keyed by step alone
lets the second entry overwrite the first, after which one whole side's
commitments are recomputed with somebody else's nonce and reported as
`TAMPERED`. That is a false accusation of cheating in the very tool a grader is
told to run, so it is pinned here rather than left to a fixture's shape.
"""

from mars777_police.app.replay_crypto import check_commit
from mars777_police.app.replay_log import read_log
from mars777_police.app.replay_values import ReplayCheck

POLICE_NONCE = "1" * 32
THIEF_NONCE = "2" * 32


def commit(role: str) -> dict[str, object]:
    """One side's commit entry for step one, shaped as the log writes it."""
    return {
        "phase": "commit",
        "commit": "a" * 64,
        "step": 1,
        "intent": "truth",
        "hint": "",
        "move": {"kind": "MOVE", "value": "S"},
        "state": {
            "config_sha256": "b" * 64,
            "self_pos": [0, 0],
            "barriers": [],
            "step": 1,
            "role": role,
        },
    }


def document() -> dict[str, object]:
    """A log whose single step holds both sides' commitments and both nonces."""
    return {
        "game_id": "A-vs-B",
        "game_uid": "u",
        "sub_game": 1,
        "config_sha256": "a" * 64,
        "entries": [commit("police"), commit("thief")],
        "audit": {
            "final_reveal": [
                {"step": 1, "role": "police", "nonce": POLICE_NONCE},
                {"step": 1, "role": "thief", "nonce": THIEF_NONCE},
            ],
            "semantic": {"verdict": "CONSISTENT"},
        },
    }


def test_both_sides_nonces_survive_a_step_they_share() -> None:
    assert read_log(document()).nonces == {
        (1, "police"): POLICE_NONCE,
        (1, "thief"): THIEF_NONCE,
    }


def test_each_side_is_checked_against_its_own_released_nonce() -> None:
    nonces = read_log(document()).nonces
    seen: list[str] = []

    class Recording:
        """A commitment port that reports which nonce it was asked to use."""

        def recompute(self, **parts: object) -> object:
            """Record the nonce and return a digest that will not match."""
            nonce = parts["nonce"]
            seen.append(getattr(nonce, "value", str(nonce)))
            return object()

        def matches(self, stored: object, recomputed: object) -> bool:
            """Never match: this test is about the input, not the verdict."""
            return False

    for entry in (commit("police"), commit("thief")):
        check_commit(entry, None, nonces, Recording(), 1)  # type: ignore[arg-type]

    assert seen == [POLICE_NONCE, THIEF_NONCE]


def test_a_side_whose_nonce_was_never_released_is_not_accused() -> None:
    partial = {(1, "thief"): THIEF_NONCE}

    assert check_commit(commit("police"), None, partial, None, 1) is (  # type: ignore[arg-type]
        ReplayCheck.NOT_CHECKABLE
    )


def test_an_unlabelled_nonce_is_ignored_rather_than_applied_to_everyone() -> None:
    document_without_roles = document()
    audit = document_without_roles["audit"]
    assert isinstance(audit, dict)
    audit["final_reveal"] = [{"step": 1, "nonce": POLICE_NONCE}]

    assert read_log(document_without_roles).nonces == {}
