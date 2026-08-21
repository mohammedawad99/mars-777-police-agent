# Expected results for every quality command

What each gate command should print, what it means when it fails, and what it
measured most recently. Run from the repository root.

**Check the exit status, not the output.** This is written down because it went
wrong: a gate run was once reported green on the strength of a grep for
pytest's summary line, and two real failures went unseen until CI caught them.
`echo $?` is the evidence; the text is a convenience.

| # | command | expected | failure means | last measured |
|---|---|---|---|---|
| 1 | `uv sync --frozen` | exit 0, lockfile unchanged | the lock and `pyproject.toml` disagree; someone added a dependency without locking it | exit 0 |
| 2 | `uv run python tools/check_python_loc.py` | exit 0, **0 files over the limit** | a file exceeds 150 *code* lines (blank lines and comments excluded, per guideline §3.2) | 0 violations |
| 3 | `uv run ruff check .` | exit 0, `All checks passed!` | a lint rule fired; fix the code, never the rule | 0 findings |
| 4 | `uv run ruff format --check .` | exit 0 | formatting drifted; run `ruff format` | clean |
| 5 | `uv run mypy --strict` | exit 0, `no issues found` | a type error, an implicit `Any`, or an untyped def | 0 errors in 295 source files |
| 6 | `uv run pytest -q --cov` | exit 0, all tests pass | see below | **4,962 collected**, 14 skipped, 0 failed |
| 7 | coverage (same run) | **100.00%** statement **and** branch | an untested line or an untaken branch | 100.00%, 0 missing, 0 partial, 11,431 statements |
| 8 | `uv build` | exit 0, sdist + wheel | packaging metadata is wrong | both built |
| 9 | `git diff --check` | exit 0, no output | whitespace damage | clean |
| 10 | secret scan | 0 real findings | a credential reached the tree | 0 (one documentation false positive, see below) |

## The 14 skipped tests are deliberate, and named

Skips are not failures and are not silent: each states its condition.

| skipped | why |
|---|---|
| 13 × `tests/network/test_live_*` | need a real tunnel: `MARS777_RUN_LIVE_NGROK=1` plus an installed agent |
| 1 × `tests/reporting/test_live_gmail.py` | needs explicit operator authorisation: `MARS777_RUN_LIVE_GMAIL=1` plus a token and a recipient |

Nothing is skipped to make a suite pass. Both groups require an external
resource that must never be contacted without an operator asking for it.

## Gates with a specific expected count

| check | expected |
|---|---|
| exact-six counted series | **6** sub-games, **6** `CONSISTENT` audits, **14** official artifacts per side |
| official artifact families | `declaration_` 1 · `config_` 6 · `log_` 6 · `result_` 1 |
| research corpus | 4,988 unique development-headline scenarios; final holdout **2,226**, evaluated **once** |
| decision latency | p95 **≤ 25 ms**; measured 2.28 ms (`grid9`) / 3.34 ms (`grid11`) |

## The one secret-scan finding, and why it is not one

The pattern `client_secret` matches a line in `docs/GUIDELINE_ALIGNMENT.md`
that documents the `.gitignore` entry `client_secret*.json`. It is prose naming
a filename pattern; no credential exists in the tree or in history. It is
recorded here rather than suppressed, so the next reader does not have to
re-derive it.

## Cross-platform expectation

Ubuntu runs the whole suite. Windows runs the whole suite **except one test** —
the documented native two-process exact-six stall — which runs in its own
**visible, non-gating** job. That exclusion is a known platform limitation
recorded in `CONCURRENCY_MODEL.md` §6, not a way of making Windows pass.
