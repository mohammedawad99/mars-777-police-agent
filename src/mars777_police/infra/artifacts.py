"""Writing an official artifact so that a half-written one can never be read.

`infra.artifacts` is the registered home of `ArtifactStorePort`. It owns bytes
and the filesystem, and nothing else: it never decides what an artifact means,
which family it belongs to, or whether its values are true.

**A reader only ever sees a complete file.** Each write goes to a temporary
sibling in the same directory, is flushed to the device, and is then moved onto
the official name with `os.replace`, which is atomic on POSIX and Windows alike.
The sibling matters as much as the flush: `os.replace` is only atomic within one
filesystem, and a temp directory may be another one.

**A retry is safe; a contradiction is not.** Re-writing byte-identical content is
success - the evidence already on disk is the evidence we were asked to write.
Different content under a name that already exists is refused, because an
official artifact that changed its mind is worse than a missing one.

**Deterministic, but not the hashing canonicalization.** `protocol.canonical`
serializes what gets *hashed* and deliberately refuses `None`; artifacts
legitimately carry `null` (`entries[].verified`, `audit.tampered_step`). So the
bytes here are sorted-key, tight-separator UTF-8 JSON, and the hashing contract
is left exactly as it is.
"""

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

from ..app.artifact_store import ArtifactDocument, StoredArtifact
from ..app.protocol_errors import LocalDefectError
from ..app.protocol_values import Sha256Digest

ENCODING = "utf-8"
SUFFIX = ".partial"
"""What an interrupted write leaves behind - never an official filename."""


def serialize(document: ArtifactDocument) -> bytes:
    """Return the one deterministic byte form of *document*."""
    text = json.dumps(dict(document), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode(ENCODING)


@dataclass(frozen=True, slots=True)
class JsonArtifactStore:
    """The production `ArtifactStorePort`, rooted at one explicit directory.

    The root is supplied by outer production code and never inferred: nothing
    here reads the working directory, an environment variable or a setting.
    """

    root: Path

    def store(self, name: str, document: ArtifactDocument) -> StoredArtifact:
        """Persist *document* as *name*, atomically, idempotently, once."""
        content = serialize(document)
        target = self.root / name
        existing = self._existing(target)
        if existing is not None:
            if existing != content:
                raise LocalDefectError(
                    f"{name} already exists with different content;"
                    " an official artifact is never overwritten",
                )
            return _stored(target, content)
        self.root.mkdir(parents=True, exist_ok=True)
        self._replace(target, content)
        return _stored(target, content)

    def _existing(self, target: Path) -> bytes | None:
        """The bytes already stored under *target*, or `None` if it is unwritten."""
        try:
            return target.read_bytes()
        except FileNotFoundError:
            return None

    def _replace(self, target: Path, content: bytes) -> None:
        """Write beside *target*, then move onto it in one atomic step."""
        with NamedTemporaryFile(
            dir=self.root, prefix=f"{target.name}.", suffix=SUFFIX, delete=False
        ) as handle:
            partial = Path(handle.name)
            try:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            except BaseException:
                handle.close()
                partial.unlink(missing_ok=True)
                raise
        try:
            os.replace(partial, target)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise


def _stored(target: Path, content: bytes) -> StoredArtifact:
    """Describe what is now on disk: where it is and what it hashes to."""
    return StoredArtifact(str(target), Sha256Digest(sha256(content).hexdigest()))
