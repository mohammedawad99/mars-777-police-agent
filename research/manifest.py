"""What a grader needs to reproduce the baseline without guessing an input.

Every ingredient of a benchmark is identified by a hash rather than a
description, so "the same corpus" is a checkable claim: the seed banks, the
opponent corpus, the configuration corpus, the strategy sources and the commit
they came from. If any of them changes, the manifest changes with it.
"""

import hashlib
from dataclasses import dataclass

from .configs import digest_source
from .identity import BaselineIdentity, baseline_identity
from .opponents import FAMILIES, OBSERVATION_BUDGET
from .records import SCHEMA_VERSION
from .seeds import NAMESPACE, banks

ANALYSIS_VERSION = "analysis-1"
REPRODUCE = "uv run python -m research.bench_main all --out results"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Manifest:
    """The complete identity of one benchmark run's inputs."""

    identity: BaselineIdentity

    def as_document(self) -> dict[str, object]:
        """The manifest as a deterministic JSON-ready document."""
        return {
            "schema": SCHEMA_VERSION,
            "analysis": ANALYSIS_VERSION,
            "baseline": self.identity.as_record(),
            "seed_namespace": NAMESPACE,
            "seed_banks": {
                one.name: {"size": len(one.seeds), "sha256": one.digest} for one in banks()
            },
            "opponent_corpus": {
                "families": list(FAMILIES),
                "observation_budget": OBSERVATION_BUDGET,
                "sha256": _hash("|".join(FAMILIES)),
            },
            "config_corpus_sha256": _hash(digest_source()),
            "reproduce": REPRODUCE,
        }


def manifest() -> Manifest:
    """The manifest for this repository's frozen baseline."""
    return Manifest(baseline_identity())
