"""What the candidate figures must show, including the parts that lost.

A figure is evidence, so these assert the properties that make it honest: a real
zero line for a signed quantity, every candidate present, and the rejected ones
marked rather than dropped.
"""

import json
from pathlib import Path

import pytest
from research.curve import Point, progression
from research.delta_chart import Delta, diverging
from research.gates import ADVANCED, REJECTED_GATE

KEPT = Delta("C4", 0.0722, 0.0446, 0.1019, 471, True, ADVANCED)
LOST = Delta("C1", -0.0488, -0.0679, -0.0318, 471, False, REJECTED_GATE)


def test_a_loss_and_a_gain_of_equal_size_draw_equally_long() -> None:
    """The symmetry that stops a sign from changing the apparent magnitude."""
    frame = diverging(
        "t",
        "u",
        (Delta("up", 0.05, 0.04, 0.06, 9, True), Delta("down", -0.05, -0.06, -0.04, 9, False)),
        "c",
    )
    bars = [one for one in frame.rects if one.fill in ("#4d7fff", "#c2453c")]

    assert bars[0].width == bars[1].width


def test_a_negative_candidate_is_drawn_on_the_losing_side_of_zero() -> None:
    frame = diverging("t", "u", (LOST,), "c")
    bar = next(one for one in frame.rects if one.fill == "#c2453c")
    zero = next(one for one in frame.rects if one.fill == "#39424e" and one.width == 1)

    assert bar.left + bar.width <= zero.left + 1


def test_every_candidate_label_stays_on_the_canvas() -> None:
    """The first draft ran C4's label off the right edge, so it is asserted."""
    frame = diverging("t", "u", (KEPT, LOST), "c")

    for text in frame.texts:
        assert 0 <= text.left <= frame.width - 1


def test_a_figure_refuses_to_draw_nothing() -> None:
    with pytest.raises(ValueError, match="at least one"):
        diverging("t", "u", (), "c")
    with pytest.raises(ValueError, match="at least one"):
        progression("t", "u", (), "c")


def test_the_progression_marks_rejected_points_differently_from_kept_ones() -> None:
    frame = progression(
        "t", "u", (Point("C1", -0.05, REJECTED_GATE), Point("C4", 0.07, ADVANCED)), "c"
    )
    colours = {one.fill for one in frame.rects}

    assert "#c2453c" in colours
    assert "#4d7fff" in colours


def test_the_progression_says_it_is_not_training() -> None:
    """The one caption this project may never get wrong."""
    frame = progression("Police exploration", "delta", (Point("C1", 0.01, ADVANCED),), "cap")
    words = " ".join(one.value for one in frame.texts).lower()

    assert "not time or epochs" in words
    assert "loss" not in words
    assert "epoch" not in words.replace("epochs", "")


def test_the_progression_puts_zero_where_zero_is() -> None:
    """A signed quantity on a shifted origin flattens the search; this forbids it."""
    frame = progression("t", "u", (Point("a", 0.0, ADVANCED), Point("b", 0.0, ADVANCED)), "c")
    marked = [one for one in frame.texts if "no change" in one.value]
    dots = [one for one in frame.rects if one.fill == "#4d7fff"]

    assert marked
    assert abs(dots[0].top - marked[0].top) <= 10


def test_a_bar_that_is_not_a_candidate_carries_no_verdict_word() -> None:
    """An opponent family is not a candidate, so it is not "advanced"."""
    frame = diverging("t", "u", (Delta("evasive", 0.07, 0.04, 0.10, 317, True),), "c")
    said = " ".join(one.value for one in frame.texts)

    assert "advanced" not in said
    assert "rejected" not in said
    assert "+0.0700" in said


def test_a_candidate_bar_keeps_the_status_it_earned() -> None:
    frame = diverging("t", "u", (KEPT, LOST), "c")
    said = " ".join(one.value for one in frame.texts)

    assert ADVANCED.lower() in said
    assert REJECTED_GATE.lower() in said


def test_an_older_result_document_is_read_without_being_rewritten(tmp_path: Path) -> None:
    """Stage 9B-1A wrote `win_delta` beside a separate `paired_ci`.

    Rewriting a frozen measurement to match a newer layout would change its
    digest for a cosmetic reason, so both shapes are read instead.
    """
    from research.evidence_figures import _read

    path = tmp_path / "full_C4.json"
    path.write_text(
        json.dumps(
            {
                "overall": {"n": 2247, "win_delta": 0.06008},
                "paired_ci": {"ci_low": 0.046729, "ci_high": 0.074766},
                "family": {},
                "config": {},
            }
        ),
        encoding="utf-8",
    )

    found = _read(path)

    assert found["overall"]["delta"] == 0.06008
    assert found["overall"]["ci_low"] == 0.046729
    assert found["overall"]["ci_high"] == 0.074766


def test_the_evidence_figures_work_before_a_holdout_result_exists(tmp_path: Path) -> None:
    """The one-shot point is optional: it is drawn only once it has been recorded."""
    from research.evidence_figures import write_all

    cell = {"n": 9, "delta": 0.06, "ci_low": 0.04, "ci_high": 0.08}
    result = {
        "overall": dict(cell),
        "family": {"evasive": dict(cell)},
        "config": {"grid7": dict(cell)},
    }
    candidates = tmp_path / "candidates"
    candidates.mkdir(parents=True)
    for name in ("full", "validation", "stress"):
        (candidates / f"{name}_C4.json").write_text(json.dumps(result), encoding="utf-8")
    (candidates / "screening.json").write_text(
        json.dumps(
            {
                "screening": {"n": 9},
                **{
                    key: {
                        "revision": "r1",
                        "summary": key,
                        "overall": {
                            "n": 9,
                            "baseline_wins": 1,
                            "candidate_wins": 2,
                            "gains": 1,
                            "losses": 0,
                        },
                        "paired_ci": {"mean": 0.01, "ci_low": 0.0, "ci_high": 0.02},
                    }
                    for key in ("C1", "C2", "C3", "C4")
                },
            }
        ),
        encoding="utf-8",
    )

    written = write_all(tmp_path)

    drawn = sorted(one.name for one in written)
    assert "c4_final_holdout_family.png" not in drawn
    assert "strategy_research_progression.png" in drawn
