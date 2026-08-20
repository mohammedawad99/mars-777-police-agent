"""Exactly which strategy was measured, pinned so a result can be re-checked.

A benchmark number is meaningless without the identity of what produced it, and
a class name is not an identity: two revisions share it. So a baseline is
recorded as its module, its class, the SHA-256 of the source files that define
it, and the repository commit those files came from.

**Nothing here imports a strategy to describe it.** The composition root already
names the production policy; this reads the file, so a benchmark cannot silently
measure something the agent does not actually ship.
"""

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "mars777_police"
ROLE = "police"

PRODUCTION_STRATEGY = "CompetitiveStrategy"
"""Resolved mechanically from `composition.py`, never from memory."""

SOURCES = ("app/competitive_strategy.py", "app/baseline_strategy.py")
"""Every file the production policy is defined by, in dependency order."""


@dataclass(frozen=True, slots=True)
class BaselineIdentity:
    """What was measured, precisely enough to measure it again."""

    role: str
    package: str
    strategy: str
    sources: tuple[str, ...]
    source_sha256: str
    commit: str

    def as_record(self) -> dict[str, str]:
        """The identity as flat text, for a result record or a manifest."""
        return {
            "role": self.role,
            "package": self.package,
            "strategy": self.strategy,
            "sources": ",".join(self.sources),
            "source_sha256": self.source_sha256,
            "commit": self.commit,
        }


def digest_of(paths: tuple[str, ...]) -> str:
    """One SHA-256 over the named source files, in the order given.

    Order is part of the identity rather than sorted away: the files are listed
    in dependency order, and a benchmark that reordered them would report a
    different digest for the same code.
    """
    running = hashlib.sha256()
    for name in paths:
        running.update((ROOT / "src" / PACKAGE / name).read_bytes())
    return running.hexdigest()


def commit_of() -> str:
    """The repository commit these sources came from, or `unknown` outside git."""
    try:
        found = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return found.stdout.strip() or "unknown"


def baseline_identity() -> BaselineIdentity:
    """The frozen identity of the strategy this repository actually ships."""
    return BaselineIdentity(
        role=ROLE,
        package=PACKAGE,
        strategy=PRODUCTION_STRATEGY,
        sources=SOURCES,
        source_sha256=digest_of(SOURCES),
        commit=commit_of(),
    )
