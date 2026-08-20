"""The counting rule itself, case by case.

Guideline §3.2 caps a file at 150 **code** lines and says blank lines and
comment lines are not counted; §6.1 rule 6 applies the same cap to test files.
Everything else in a file is code - including docstrings, which §3.3 requires and
which are statements, not comments. A checker that quietly excluded them would
reward deleting documentation to pass a size gate.
"""

from check_python_loc import LIMIT, effective_code_lines


def test_the_limit_is_the_one_the_guideline_names() -> None:
    assert LIMIT == 150


def test_an_empty_file_has_no_code() -> None:
    assert effective_code_lines("") == 0


def test_blank_lines_are_not_counted() -> None:
    assert effective_code_lines("x = 1\n\n\n\ny = 2\n") == 2


def test_whitespace_only_lines_are_not_counted() -> None:
    assert effective_code_lines("x = 1\n   \n\t\ny = 2\n") == 2


def test_comment_only_lines_are_not_counted() -> None:
    assert effective_code_lines("# a note\nx = 1\n    # indented note\n") == 1


def test_a_line_with_code_and_a_trailing_comment_is_counted() -> None:
    assert effective_code_lines("x = 1  # why\n") == 1


def test_a_noqa_or_type_comment_does_not_erase_its_code_line() -> None:
    source = "import os  # noqa: F401\ny = 1  # type: int\n"

    assert effective_code_lines(source) == 2


def test_docstring_lines_are_counted() -> None:
    source = '"""One.\n\nThree.\n"""\nx = 1\n'

    assert effective_code_lines(source) == 4


def test_a_hash_inside_a_string_is_not_a_comment() -> None:
    source = 'x = "# not a comment"\n'

    assert effective_code_lines(source) == 1


def test_every_line_of_a_multiline_expression_is_counted() -> None:
    source = "value = (\n    1\n    + 2\n)\n"

    assert effective_code_lines(source) == 4


def test_a_decorator_is_a_code_line() -> None:
    source = "import functools\n\n\n@functools.cache\ndef f() -> int:\n    return 1\n"

    assert effective_code_lines(source) == 4


def test_a_blank_line_inside_a_docstring_is_still_blank() -> None:
    """The rule is physical: a blank line is blank wherever it sits."""
    assert effective_code_lines('"""A.\n\nB."""\n') == 2


def test_exactly_the_limit_is_allowed() -> None:
    assert effective_code_lines("x = 1\n" * LIMIT) == LIMIT


def test_one_line_over_the_limit_is_over() -> None:
    assert effective_code_lines("x = 1\n" * (LIMIT + 1)) == LIMIT + 1
