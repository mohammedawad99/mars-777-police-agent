"""Physical ownership of the peer-message semantic values (Stage 4E-R7).

`app.peer_messages` reached 150/150 LOC holding all four values, so no further
family fitted. Stage 4E-R6 froze the split: `app.turn_cursor` owns the shared
turn identity, `app.peer_turn_messages` owns the per-turn families,
`app.peer_final_messages` is the finalization boundary, and `app.peer_messages`
becomes a **façade** re-exporting the *same class objects*.

This file tests the *layout* only. Behaviour is owned by the existing
`test_peer_messages.py`, `test_acknowledgement.py` and `test_reveal.py`, which
must keep passing **unchanged** - that is the migration's real acceptance test.
The façade must therefore expose no wrapper, no subclass and no second
definition, and must still not name any blocked family.
"""

import ast
import inspect
from pathlib import Path

import pytest

from mars777_police.app import (
    peer_final_messages,
    peer_messages,
    peer_turn_messages,
    turn_cursor,
)

DEFINING = {
    "TurnCursor": turn_cursor,
    "Commitment": peer_turn_messages,
    "Acknowledgement": peer_turn_messages,
    "Reveal": peer_turn_messages,
    "NonceRevealEntry": peer_final_messages,
    "FinalNonceReveal": peer_final_messages,
}
FACADE_NAMES = ("TurnCursor", "Commitment", "Acknowledgement", "Reveal", "FinalNonceReveal")
APP_DIR = Path(inspect.getfile(peer_messages)).parent


def _classes_defined_in(module: object) -> set[str]:
    tree = ast.parse(inspect.getsource(module))  # type: ignore[arg-type]
    return {n.name for n in tree.body if isinstance(n, ast.ClassDef)}


@pytest.mark.parametrize("name", sorted(DEFINING))
def test_each_value_has_exactly_one_definition_in_its_owning_module(name: str) -> None:
    """One definition, possibly several import paths - never two classes."""
    owners = [
        m
        for m in (turn_cursor, peer_turn_messages, peer_final_messages)
        if name in _classes_defined_in(m)
    ]
    assert owners == [DEFINING[name]]


@pytest.mark.parametrize("name", FACADE_NAMES)
def test_the_facade_re_exports_the_same_class_object(name: str) -> None:
    """`NonceRevealEntry` is a supporting value, so it stays off the façade."""
    assert getattr(peer_messages, name) is getattr(DEFINING[name], name)
    assert not hasattr(peer_messages, "NonceRevealEntry")


@pytest.mark.parametrize("name", sorted(DEFINING))
def test_the_app_surface_re_exports_the_same_class_object(name: str) -> None:
    from mars777_police import app

    assert getattr(app, name) is getattr(DEFINING[name], name)


def test_the_facade_defines_no_class_of_its_own() -> None:
    """A façade that defined a wrapper or subclass would be a second truth."""
    assert _classes_defined_in(peer_messages) == set()


def test_the_finalization_module_owns_exactly_the_end_of_series_values() -> None:
    """R7 left this boundary empty; R8 filled it, and R15 added the series close.

    ``ResultAgreement`` belongs here because it *is* the end-of-series peer
    family. Its supporting values stay in ``app.result_values`` - the boundary
    owns families, never their parts.
    """
    assert _classes_defined_in(peer_final_messages) == {
        "NonceRevealEntry",
        "FinalNonceReveal",
        "ResultAgreement",
    }
    for support in ("NonceValue", "InvalidNonceError", "ResultContribution", "GitCommitSha"):
        assert support not in _classes_defined_in(peer_final_messages)


def test_the_public_import_paths_still_work_unchanged() -> None:
    """The exact import three committed test modules already use."""
    from mars777_police.app.peer_messages import (
        Acknowledgement,
        Commitment,
        Reveal,
        TurnCursor,
    )

    assert (TurnCursor, Commitment, Acknowledgement, Reveal) == (
        turn_cursor.TurnCursor,
        peer_turn_messages.Commitment,
        peer_turn_messages.Acknowledgement,
        peer_turn_messages.Reveal,
    )


def _sibling_imports(module: object) -> set[str]:
    """The app-sibling modules *imported* by this one - prose is not an edge."""
    tree = ast.parse(inspect.getsource(module))  # type: ignore[arg-type]
    return {
        n.module
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.level == 1 and n.module
    }


def test_the_defining_modules_do_not_import_the_facade() -> None:
    """Direction is turn_cursor <- turn/final <- façade; a back edge would cycle."""
    assert "peer_messages" not in _sibling_imports(turn_cursor)
    assert "peer_messages" not in _sibling_imports(peer_turn_messages)
    assert "peer_messages" not in _sibling_imports(peer_final_messages)
    assert _sibling_imports(turn_cursor) == set()
    assert _sibling_imports(peer_turn_messages) == {
        "capture_values",
        "protocol_values",
        "turn_cursor",
    }
    assert _sibling_imports(peer_final_messages) == {
        "artifact_values",
        "protocol_values",
        "result_values",
        "turn_cursor",
    }


def test_every_peer_message_module_stays_within_the_line_budget() -> None:
    """The capacity blocker is only removed if each new home has real headroom."""
    for name in ("turn_cursor", "peer_turn_messages", "peer_final_messages", "peer_messages"):
        lines = len((APP_DIR / f"{name}.py").read_text(encoding="utf-8").splitlines())
        assert lines <= 150, f"{name}.py is {lines} LOC"
    facade = len((APP_DIR / "peer_messages.py").read_text(encoding="utf-8").splitlines())
    assert facade <= 60
