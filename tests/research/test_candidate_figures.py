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

from research import candidate_tables

KEPT = Delta("C4", 0.0722, 0.0446, 0.1019, 471, True)
LOST = Delta("C1", -0.0488, -0.0679, -0.0318, 471, False)


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
    frame = progression("t", "u", (Point("C1", -0.05, False), Point("C4", 0.07, True)), "c")
    colours = {one.fill for one in frame.rects}

    assert "#c2453c" in colours
    assert "#4d7fff" in colours


def test_the_progression_says_it_is_not_training() -> None:
    """The one caption this project may never get wrong."""
    frame = progression("Police exploration", "delta", (Point("C1", 0.01, True),), "cap")
    words = " ".join(one.value for one in frame.texts).lower()

    assert "not time or epochs" in words
    assert "loss" not in words
    assert "epoch" not in words.replace("epochs", "")


def test_the_progression_puts_zero_where_zero_is() -> None:
    """A signed quantity on a shifted origin flattens the search; this forbids it."""
    frame = progression("t", "u", (Point("a", 0.0, True), Point("b", 0.0, True)), "c")
    marked = [one for one in frame.texts if "no change" in one.value]
    dots = [one for one in frame.rects if one.fill == "#4d7fff"]

    assert marked
    assert abs(dots[0].top - marked[0].top) <= 10


def test_the_rows_carry_every_candidate_in_the_order_tried(tmp_path: Path) -> None:
    document = {
        "screening": {"n": 471},
        **{
            key: {
                "revision": "r1",
                "summary": key,
                "overall": {
                    "n": 471,
                    "baseline_wins": 23,
                    "candidate_wins": 1,
                    "gains": 1,
                    "losses": 1,
                },
                "paired_ci": {"mean": 0.01, "ci_low": 0.0, "ci_high": 0.02},
            }
            for key in candidate_tables.ORDER
        },
    }
    source = tmp_path / "screening.json"
    source.write_text(json.dumps(document), encoding="utf-8")

    written = candidate_tables.write_all(source, tmp_path)

    rows = (tmp_path / "tables" / "candidates" / "screening.csv").read_text(encoding="utf-8")
    assert [one.name for one in written] == [
        "screening.csv",
        "candidate_delta.png",
        "exploration_progression.png",
    ]
    for key in candidate_tables.ORDER:
        assert key in rows
    assert rows.count("rejected") == len(candidate_tables.ORDER) - len(candidate_tables.KEPT)


def test_the_committed_figures_carry_the_development_only_label() -> None:
    assert "NOT FINAL HOLDOUT" in candidate_tables.LABEL
    assert "NOT PRODUCTION PROMOTION" in candidate_tables.LABEL
