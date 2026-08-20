"""The 150-code-line gate, measured the way the guideline defines it.

Guideline §3.2 caps every code file at **150 code lines**, with blank lines and
comment lines excluded, and §6.1 rule 6 applies the same cap to test files. This
is the one authority for that rule: the command a contributor runs and the
command CI runs are the same command, so a failing build is never a difference
of opinion about counting.

**What counts.** Every physical line carrying Python - statements, imports,
decorators, and each line of a multi-line expression. **Docstrings count**: they
are statements, not comments, and §3.3 requires them, so excluding them would
reward deleting documentation to pass a size gate.

**What does not.** Physical blank lines, and lines whose only content is a `#`
comment. A `#` inside a string is not a comment, which is why the file is
tokenised rather than scanned as text.

**Splitting, never compressing.** §3.2 is explicit that an oversized file is to
be split. Packing statements onto one line to pass this gate satisfies the number
and defeats the rule.
"""

import io
import sys
import tokenize
from pathlib import Path

LIMIT = 150
"""The guideline's maximum code lines per Python file."""

TREES = ("src", "tests", "research")
"""The two trees the rule covers: production and tests alike."""


def effective_code_lines(source: str) -> int:
    """Return the code lines in *source* under the guideline's definition."""
    lines = source.splitlines()
    skip = {index for index, line in enumerate(lines, 1) if not line.strip()}
    readline = io.StringIO(source).readline
    for token in tokenize.generate_tokens(readline):
        if token.type == tokenize.COMMENT and token.line.lstrip().startswith("#"):
            skip.add(token.start[0])
    return len(lines) - len(skip)


def over_limit(root: Path) -> list[tuple[str, int]]:
    """Return every in-scope file above the limit, with its count, sorted.

    Paths are rendered POSIX-style whatever the platform, so the same tree
    produces the same report - and the same sort order - on Linux and Windows.
    A gate whose output depended on the operating system would not be one.
    """
    findings: list[tuple[str, int]] = []
    for tree in TREES:
        for path in sorted((root / tree).rglob("*.py")):
            counted = effective_code_lines(path.read_text(encoding="utf-8"))
            if counted > LIMIT:
                findings.append((path.relative_to(root).as_posix(), counted))
    return sorted(findings)


def main(argv: list[str] | None = None) -> int:
    """Check one repository; return 0 when every file is within the limit."""
    arguments = sys.argv[1:] if argv is None else argv
    root = Path(arguments[0]) if arguments else Path(__file__).resolve().parent.parent
    findings = over_limit(root)
    for path, counted in findings:
        print(f"{path}: {counted} code lines (limit {LIMIT})")
    if findings:
        print(f"{len(findings)} file(s) over the {LIMIT}-code-line limit")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
