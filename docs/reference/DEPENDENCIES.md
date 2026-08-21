# Dependency and licence inventory

**Licences below were read from the installed package metadata**
(`importlib.metadata`), not copied from memory or from a website. Where a
package declares no SPDX expression, its own classifier is quoted. Nothing here
is asserted without having been checked.

## Runtime — what a tournament agent actually needs

Three, pinned exactly.

| package | version | licence | why it is here |
|---|---|---|---|
| `fastmcp` | `==3.4.6` | Apache-2.0 | the peer transport the source names; serves and calls the four MCP tools |
| `pydantic` | `==2.13.4` | MIT | wire-model validation at the transport boundary; a malformed peer message is rejected before it reaches `app` |
| `pillow` | `==11.3.0` | MIT-CMU | rasterises the GUI and every research figure headlessly, so screenshots and charts are produced on CI without a display |

**Exact `==` pins, deliberately.** A tournament result must be reproducible from
the lockfile; a range would let a rebuild play a slightly different program.

**No dependency is used for game logic.** Movement, barriers, scent, scoring and
the audit are pure project code over the standard library, so nothing in the
table above can change the outcome of a game.

**Not present, on purpose:** no HTTP client library (Gmail speaks the provider's
REST API over `urllib` from the standard library), no plotting library
(`matplotlib` was rejected — the figures reuse the tested renderer already in the
tree), no ORM, no logging framework, no LLM SDK.

## Development — not shipped

| package | constraint | licence | purpose |
|---|---|---|---|
| `pytest` | `>=8,<9` | MIT | test runner |
| `pytest-cov` | `>=5,<7` | MIT | statement + branch coverage gate |
| `coverage` | via `pytest-cov` | Apache-2.0 | the measurement itself |
| `ruff` | `>=0.6,<1.0` | MIT | lint and format |
| `mypy` | `>=1.11,<2.0` | MIT | `--strict` type checking |

Ranges rather than exact pins: these do not affect a played game, and a newer
linter finding a real defect is a benefit rather than a reproducibility risk.

## Optional `notebook` group — locked, but not installed by default

| package | constraint | licence | purpose |
|---|---|---|---|
| `jupyter` | `>=1.1,<2.0` | BSD-3-Clause | executing `notebooks/competitive_research.ipynb` |
| `nbconvert` | `>=7.16,<8.0` | BSD-3-Clause | re-executing it in place |

**Present in `uv.lock`, absent from a default install.** The group is resolved
in the lockfile, so `uv sync --group notebook` reproduces exactly one set of
versions rather than whatever PyPI offers today. It is **not** a default group,
so plain `uv sync --frozen` - what CI runs and what a tournament agent needs -
installs only the three runtime dependencies and never a notebook stack.
`uv lock --check` passes, so `pyproject.toml` and the lock agree.

The notebook's figures and tables also regenerate without Jupyter at all, so
nothing in the research evidence depends on this group being installed.

## Python

`requires-python = ">=3.12"`. Everything above is 3.12-compatible and is
exercised on 3.12 in CI on Ubuntu **and** Windows.

## The pinned third-party kit

The lecturer's reference kit is pinned at commit `ad65576` and is used **only**
as a sparring peer for interoperability evidence. It is **not** a dependency of
this package, is not imported by any production module, and is not redistributed
here. Its licence status is **not asserted by this project**; it is referenced by
commit, and any use beyond local interoperability testing would need its own
licence review.

## Verifying this table

```bash
uv run python -c "
import importlib.metadata as md
for name in ('fastmcp', 'pydantic', 'pillow', 'pytest', 'ruff', 'mypy'):
    m = md.metadata(name)
    print(name, md.version(name), m.get('License-Expression') or m.get('License'))
"
```
