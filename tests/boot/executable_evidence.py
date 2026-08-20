"""What a finished run left behind, read back and reported safely.

Artifacts on disk, log lines, and a two-process report an operator could paste
into a review - with the pre-shared secret scrubbed out of it, because a
diagnostic that leaks key material is worse than no diagnostic at all.
"""

import json
from collections.abc import Sequence
from pathlib import Path

from boot_builders import SECRET
from executable_outcome import Ran, highest
from executable_process import CONTROL_EXIT, GRACEFUL_MARKERS, WINDOWS


def official(root: Path) -> list[str]:
    """The official file names a finished side left behind, sorted."""
    return sorted(path.name for path in root.iterdir()) if root.exists() else []


def _log_lines(root: Path, names: Sequence[str]) -> list[str]:
    """What each **finalized** sub-game log already records, and nothing more."""
    lines = []
    for name in sorted(name for name in names if name.startswith("log_")):
        try:
            document = json.loads((root / name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as failure:
            lines.append(f"    {name}: unreadable ({type(failure).__name__})")
            continue
        audit = document.get("audit", {})
        lines.append(
            f"    {name}: sub_game={document.get('sub_game')}"
            f" entries={len(document.get('entries', []))}"
            f" result={audit.get('result')}"
            f" semantic={audit.get('semantic', {}).get('verdict')}"
        )
    return lines


def snapshot(name: str, root: Path) -> str:
    """One side's persisted evidence: how far it got, read from files alone.

    A sub-game's config is written when it locks and its log only when it
    finishes, so `config g06` beside `log g05` places a stall inside g06 without
    any live progress record existing. The **step** inside the active round is
    not persisted until that sub-game finalizes, so it stays unknown here rather
    than being guessed at.
    """
    names = official(root)
    declared = any(one.startswith("declaration_") for one in names)
    concluded = any(one.startswith("result_") for one in names)
    lines = [
        f"  {name} artifacts in {root}: {len(names)} file(s)",
        f"    declaration: {'yes' if declared else 'no'}",
        f"    result: {'yes' if concluded else 'no'}",
        f"    highest locked config: {highest(names, 'config_')}",
        f"    highest completed log: {highest(names, 'log_')}",
        f"    names: {names}",
    ]
    return "\n".join([*lines, *_log_lines(root, names)])


def two_process_report(runs: Sequence[Ran], roots: Sequence[tuple[str, Path]]) -> str:
    """Everything a failing two-process run knows, with the secret scrubbed.

    The scrub is belt and braces: the streams are separately asserted free of
    the synthetic secret, and this is the text a CI log would publish.
    """
    blocks = ["TWO-PROCESS DIAGNOSTIC"]
    for ran in runs:
        killed = " (killed after timeout)" if ran.timed_out else ""
        blocks.append(f"  {ran.name}: pid={ran.pid} exit={ran.status}{killed}")
    blocks.extend(snapshot(name, root) for name, root in roots)
    sse = [ran.name for ran in runs if "standalone SSE writer" in ran.err]
    accept = [ran.name for ran in runs if "IocpProactor.accept" in ran.err]
    blocks.append(f"  SSE writer error reported by: {sse or 'neither'}")
    blocks.append(f"  accept-task WinError 995 reported by: {accept or 'neither'}")
    for ran in runs:
        blocks.append(f"--- {ran.name} stdout ---\n{ran.out}")
        blocks.append(f"--- {ran.name} stderr ---\n{ran.err}")
    return _scrubbed("\n".join(blocks))


def _scrubbed(text: str) -> str:
    """The one scrubber every published diagnostic passes through."""
    return text.replace(SECRET, "<secret redacted>")


def assert_clean_operator_stop(status: int, out: str, err: str, windows: bool = WINDOWS) -> None:
    """Assert the stop was clean under *this platform's* contract.

    POSIX is exactly 0 - a control-event status there would be a real failure.
    Windows delivers `CTRL_BREAK_EVENT` through the console, which terminates the
    process on its own terms after the handlers run, so the status alone cannot
    tell a graceful shutdown from a kill; the server's own shutdown record is
    what does, and 3 is refused without it.
    """
    assert "Traceback" not in err, err
    assert SECRET not in out and SECRET not in err
    if not windows:
        assert status == 0, err
        return
    assert status in {0, CONTROL_EXIT}, err
    missing = [marker for marker in GRACEFUL_MARKERS if marker not in err]
    assert not missing, f"status {status} without a complete shutdown, missing {missing}: {err}"
