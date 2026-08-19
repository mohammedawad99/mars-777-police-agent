"""The official artifact identifier, and the group code it has to be able to name.

`NAMING_AND_IDENTITY.md` is explicit about provenance: the book **names**
`game_id` and `game_uid` (Ch 9 p.95) and does **not** fix their internal format,
so the format alone is PROJECT-CONTRACT - **JDEC-005**. The old format was
`[a-z0-9-]`, lowercase only.

That collides with two things the project does not get to change. `group_id` is
SOURCE-EXPLICIT (App E #45: exactly 8 characters, no spaces) and ours is
`MaRs-777`, uppercase included. And the kit derives `game_id` as
`"-vs-".join(sorted(pair))`, so our own group code appears inside it verbatim.
The result was an official namer that could not write a filename for a legitimate
game we had actually played.

So the **format** is amended - it is the project's to amend - and every safety
property the old rule bought is kept: no separator, no dot segment, no absolute
prefix, no whitespace, no control character can survive it.
"""

import pytest

from mars777_police import GROUP_CODE
from mars777_police.app.artifact_store import (
    InvalidArtifactNameError,
    config_name,
    declaration_name,
    log_name,
    require_game_id,
    result_name,
)
from mars777_police.protocol.kit_identity import kit_game_id

PEER = "sparring-local"
KIT_GAME_ID = f"{GROUP_CODE}-vs-{PEER}"


def official_names(game_id: str) -> list[str]:
    """The fourteen names one series is written under."""
    return [
        declaration_name(game_id),
        *(config_name(game_id, number) for number in range(1, 7)),
        *(log_name(game_id, number) for number in range(1, 7)),
        result_name(game_id),
    ]


def test_the_kit_derived_id_for_our_own_group_is_accepted() -> None:
    """The exact string a real pairing produces, not a lowercase stand-in."""
    assert kit_game_id(GROUP_CODE, PEER) == KIT_GAME_ID
    assert require_game_id(KIT_GAME_ID) == KIT_GAME_ID


def test_the_group_code_keeps_its_exact_case_through_every_official_name() -> None:
    """`MaRs-777` is source-legal and case-sensitive; nothing may fold it."""
    assert GROUP_CODE == "MaRs-777"

    for name in official_names(KIT_GAME_ID):
        assert GROUP_CODE in name
        assert "mars-777" not in name


def test_the_semantic_identifier_is_returned_unchanged_and_never_rewritten() -> None:
    """Filesystem safety refuses; it does not sanitise identity behind our back."""
    assert (
        require_game_id(KIT_GAME_ID) is KIT_GAME_ID or require_game_id(KIT_GAME_ID) == KIT_GAME_ID
    )


def test_the_kit_identifier_does_not_depend_on_which_side_derives_it() -> None:
    assert kit_game_id(GROUP_CODE, PEER) == kit_game_id(PEER, GROUP_CODE)
    assert require_game_id(kit_game_id(PEER, GROUP_CODE)) == KIT_GAME_ID


def test_one_series_produces_fourteen_unique_official_names() -> None:
    """A naming proof only - no counted artifact was produced by this test."""
    names = official_names(KIT_GAME_ID)

    assert len(names) == 14
    assert len(set(names)) == 14
    assert names[0] == f"declaration_{KIT_GAME_ID}.json"
    assert names[1] == f"config_{KIT_GAME_ID}_g01.json"
    assert names[7] == f"log_{KIT_GAME_ID}_g01.json"
    assert names[13] == f"result_{KIT_GAME_ID}.json"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "../escape",
        "x/../y",
        "a/b",
        "x\\y",
        "/absolute",
        "C:\\drive",
        ".",
        "..",
        ".hidden",
        "with space",
        "dot.json",
        "under_score",
        "semi;colon",
        "quest?ion",
        "hash#tag",
        "at@sign",
        "new\nline",
        "tab\there",
        "nul\x00byte",
        "ctrl\x01char",
        "unicode-\u00e9",
    ],
)
def test_nothing_that_could_leave_the_artifact_root_is_accepted(bad: str) -> None:
    with pytest.raises(InvalidArtifactNameError):
        require_game_id(bad)


@pytest.mark.parametrize("good", ["g-1", "mars777-vs-groupx-2026w1-uid0001", "A", "0"])
def test_the_identifiers_the_project_already_used_are_still_accepted(good: str) -> None:
    assert require_game_id(good) == good


def test_a_non_string_identifier_is_still_refused_by_type() -> None:
    with pytest.raises(InvalidArtifactNameError, match="must be a str"):
        require_game_id(7)  # type: ignore[arg-type]


def test_the_change_is_lexical_only_and_moves_no_derived_identity() -> None:
    """`game_uid`, terms and commitments are untouched by a filename rule."""
    from kit_vectors import GAME_UID, GROUPS, TERMS

    from mars777_police.protocol.kit_identity import kit_game_uid

    assert kit_game_uid(TERMS, *GROUPS) == GAME_UID
