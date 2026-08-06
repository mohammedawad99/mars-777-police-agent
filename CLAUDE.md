# CLAUDE.md - Operating Contract (POLICE agent, group MaRs-777)

**Every Claude Code session MUST read this file before doing any work.**

This repository is the **POLICE** agent of the 2026 Distributed Police-Thief
P2P final project. The objective is the highest possible grade, which requires
exact compliance with book v3.0.0, production-grade engineering, strong
competitive strategy, and flawless delivery - simultaneously.

## Hard rules

- Operate **only** inside this repository (`mars-777-police-agent`).
- **Never** inspect, read, import, or modify the sibling **THIEF**
  repository (`mars-777-thief-agent`) - not its code, config, logs, runtime state,
  strategy, or secrets.
- Use `.project-spec/police_thief_p2p.pdf` as the authoritative local book copy.
- Treat book **version 3.0.0** as the primary source.
- Treat **Appendix E** as the mandatory rule / prohibition / sanction mapping.
- Treat **Appendix F** as the only authority for numeric values and statuses.
- Treat example / simulator code as **non-binding** unless explicitly marked mandatory.
- **Never implement before an approved plan.**
- **Never commit or push** without an explicit, dedicated instruction.
- Never weaken, skip, or delete a test merely to make it pass.
- Never add a dependency without explaining why it is required.
- Never add secrets, credentials, tokens, API keys, SSH keys, or OAuth files.
- **Never delegate movement legality to an LLM** - legality is deterministic code.
- Never hard-code a value that belongs in negotiated / signed configuration.
- Keep every Python source file **at or below 150 lines**.
- Add tests for **every** behavior change.
- Run all required quality gates before reporting completion.
- Report exact commands and exact results; state clearly what was **not** verified.
- Never claim a stage is complete merely because code was written.
- Preserve the exact, case-sensitive group code `MaRs-777`.
- Preserve strict role separation (this repo is **POLICE**, never THIEF).
- On any source conflict, **stop** and record it in `docs/CONFLICT_REGISTER.md`.

## Quality gates (all must pass before "done")

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
uv build
```

## Mandatory stage-report structure

Every stage must end with a report containing at least:

1. **Final status** - PASS / PARTIAL / BLOCKED (never PASS unless every
   requirement is met).
2. **What was done** - exact scope.
3. **Commands executed** - exact commands, working directory, and results
   (including failures).
4. **Verification** - quality-gate results with real numbers.
5. **What was NOT verified** - explicit unknowns and assumptions.
6. **Changes made** - files created/modified/deleted, inside and outside the repo.
7. **Isolation & safety** - confirmation that no sibling state, secret, or remote
   action was involved unless explicitly instructed.
8. **Next step** - proposed, not executed, until approved.

## Never-do summary

No remote creation, commit, push, tag, collaborator change, secret, or
cross-agent access without an explicit, dedicated instruction.
