"""The infrastructure freeze: what strategy work is allowed to touch, and nothing else.

Stage E replaces the competitive policy. That is a **behavioural** change to one
decision function, and it must not become a change to the protocol, the wire, the
artifact schema or an agreed interop constant - all of which a peer has already
verified and a grader will re-verify. The two are easy to conflate: a strategy
that needs one more field, one more helper, one small canonicalisation tweak, and
the frozen bytes move without anyone deciding that they should.

So the boundary is made checkable rather than remembered. Everything under `src/`
is frozen at a recorded digest except the few files this manifest names mutable;
a frozen file that changed, a file that disappeared, and a file that appeared are
each reported separately, because they are different mistakes with different
fixes.

**The manifest is not authority over correctness** - the tests are. It is
authority over *scope*: it answers "did this change reach further than it was
supposed to", which no individual test can see.

Refreshing it is a deliberate act (`--refresh`) that a reviewer sees in the diff,
never a side effect of running the check.
"""

import hashlib
import json
import sys
from pathlib import Path

MANIFEST = "config/infrastructure_freeze.json"
TREE = "src"

MUTABLE = ("app/competitive_strategy.py",)
"""What strategy work may change: the competitive policy, and only that.

Named rather than discovered, and the same list in both repositories. A file
here that does not exist yet is not an error - this repository may ship the
baseline today and gain a competitive policy later, and declaring it mutable in
advance means that arrival is a strategy change rather than a freeze breach.

`baseline_strategy` is deliberately **not** here. It is the reference every
candidate is measured against, so changing it silently rebases every comparison
this project has published - including ones already reported.
"""


def package(root: Path) -> Path:
    """The one distributed package directory under `src/`."""
    found = [one for one in (root / TREE).iterdir() if one.is_dir() and one.name.startswith("mars")]
    if len(found) != 1:
        raise SystemExit(f"expected exactly one package under {TREE}/, found {found}")
    return found[0]


def digests(root: Path) -> dict[str, str]:
    """Every frozen file under the package, by repository-relative path."""
    base = package(root)
    mutable = {(base / name).resolve() for name in MUTABLE}
    found: dict[str, str] = {}
    for path in sorted(base.rglob("*.py")):
        if path.resolve() in mutable or "__pycache__" in path.parts:
            continue
        found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def compare(recorded: dict[str, str], found: dict[str, str]) -> list[str]:
    """Every difference, named by the kind of mistake it is."""
    problems = []
    for path in sorted(set(recorded) - set(found)):
        problems.append(f"REMOVED  {path}")
    for path in sorted(set(found) - set(recorded)):
        problems.append(f"ADDED    {path} (frozen by default; refresh only on purpose)")
    for path in sorted(set(recorded) & set(found)):
        if recorded[path] != found[path]:
            problems.append(f"CHANGED  {path}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Check the tree against the manifest, or rewrite it when asked explicitly."""
    arguments = sys.argv[1:] if argv is None else argv
    root = Path(__file__).resolve().parent.parent
    manifest = root / MANIFEST
    found = digests(root)

    if "--refresh" in arguments:
        manifest.write_text(json.dumps(found, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"infrastructure freeze refreshed: {len(found)} files")
        return 0

    if not manifest.exists():
        print(f"no infrastructure freeze recorded at {MANIFEST}; run with --refresh")
        return 1

    problems = compare(json.loads(manifest.read_text(encoding="utf-8")), found)
    for problem in problems:
        print(problem)
    if problems:
        print(f"\n{len(problems)} infrastructure file(s) moved outside the mutable set")
        print(f"mutable: {', '.join(MUTABLE)}")
        return 1
    present = sum(1 for name in MUTABLE if (package(root) / name).is_file())
    print(f"infrastructure freeze intact: {len(found)} frozen, {present} mutable present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
