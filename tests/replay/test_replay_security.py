"""The viewer reads files somebody else wrote, so the reader is a boundary."""

from pathlib import Path

import pytest

from mars777_police.app.replay_values import ReplayError
from mars777_police.infra.replay_files import MAX_BYTES, contained, read_document


def test_a_path_inside_the_root_is_accepted(tmp_path: Path) -> None:
    inside = tmp_path / "police" / "log.json"
    inside.parent.mkdir()
    inside.write_text("{}", encoding="utf-8")

    assert contained(inside, tmp_path) == inside.resolve()


def test_the_root_itself_is_inside_itself(tmp_path: Path) -> None:
    assert contained(tmp_path, tmp_path) == tmp_path.resolve()


def test_a_traversal_out_of_the_root_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()

    with pytest.raises(ReplayError, match="outside the evidence root"):
        contained(root / ".." / "secrets.json", root)


def test_a_sibling_directory_is_refused(tmp_path: Path) -> None:
    root, other = tmp_path / "evidence", tmp_path / "elsewhere"
    root.mkdir()
    other.mkdir()

    with pytest.raises(ReplayError, match="outside the evidence root"):
        contained(other / "log.json", root)


def test_a_symlink_pointing_out_of_the_root_is_refused(tmp_path: Path) -> None:
    """Containment is resolved, so a link is judged by where it lands."""
    root, outside = tmp_path / "evidence", tmp_path / "outside.json"
    root.mkdir()
    outside.write_text("{}", encoding="utf-8")
    link = root / "log.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):  # pragma: no cover - unprivileged Windows
        pytest.skip("this platform does not allow creating a symlink here")

    with pytest.raises(ReplayError, match="outside the evidence root"):
        read_document(link, root)


def test_a_file_larger_than_the_ceiling_is_refused(tmp_path: Path) -> None:
    big = tmp_path / "log.json"
    big.write_text("[" + "0," * (MAX_BYTES // 2) + "0]", encoding="utf-8")

    with pytest.raises(ReplayError, match="larger than this viewer will read"):
        read_document(big, tmp_path)


def test_a_document_that_is_not_an_object_is_refused(tmp_path: Path) -> None:
    listed = tmp_path / "log.json"
    listed.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ReplayError, match="does not hold a JSON object"):
        read_document(listed, tmp_path)


def test_reading_without_a_root_still_refuses_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ReplayError, match="cannot read"):
        read_document(tmp_path / "absent.json")


def test_a_directory_handed_to_the_reader_is_refused(tmp_path: Path) -> None:
    """`stat` succeeds on a directory; reading it does not."""
    folder = tmp_path / "police"
    folder.mkdir()

    with pytest.raises(ReplayError, match="cannot read"):
        read_document(folder, tmp_path)
