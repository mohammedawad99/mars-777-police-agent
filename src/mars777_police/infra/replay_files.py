"""Reading evidence a viewer was handed, defensively.

The Replay Viewer is the one place this project reads files somebody else may
have written, so the reader is the security boundary: a path must stay inside
the evidence root it was given, a file must not be unbounded, and bytes that are
not JSON are a refusal rather than an exception nobody expected.

**Containment is resolved, not compared.** `resolve()` follows symlinks first,
so a link pointing outside the root is refused by the same check that refuses
`../` - there is no second rule to keep in step.
"""

import json
from pathlib import Path
from typing import Final

from ..app.replay_values import ReplayError

MAX_BYTES: Final[int] = 8 * 1024 * 1024
"""A generous ceiling for one artifact; a six-game series writes a few hundred KB."""


def contained(path: Path, root: Path) -> Path:
    """Return *path* resolved, refusing anything that leaves *root*."""
    resolved, base = path.resolve(), root.resolve()
    if resolved != base and base not in resolved.parents:
        raise ReplayError(f"{path} is outside the evidence root {root}")
    return resolved


def read_document(path: Path, root: Path | None = None) -> dict[str, object]:
    """Read one JSON evidence file, or refuse it with a reason."""
    target = path if root is None else contained(path, root)
    try:
        size = target.stat().st_size
    except OSError as failure:
        raise ReplayError(f"cannot read {path}") from failure
    if size > MAX_BYTES:
        raise ReplayError(f"{path} is larger than this viewer will read ({size} bytes)")
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except OSError as failure:
        raise ReplayError(f"cannot read {path}") from failure
    except json.JSONDecodeError as failure:
        raise ReplayError(f"{path} is not valid JSON: {failure.msg}") from failure
    if not isinstance(document, dict):
        raise ReplayError(f"{path} does not hold a JSON object")
    return document
