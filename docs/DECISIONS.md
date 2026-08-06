# Decisions Log - group MaRs-777

> **Status: DRAFT.** Records approved decisions with rationale.

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Develop on WSL2 native ext4 | Correct LF handling + performance; avoids /mnt/c and cloud-sync issues |
| D2 | Parent directory is NOT a Git repository | Prevents a super-repo nesting both agents |
| D3 | Two fully independent repositories | Enforces role isolation; no shared live state |
| D4 | Lowercase repository slugs | Filesystem-safe; group code `MaRs-777` preserved in metadata/docs |
| D5 | Exact group code `MaRs-777` preserved | Required identity; case-sensitive |
| D6 | Per-repository uv environments (`.venv`) | No shared interpreter or dependencies between agents |
| D7 | LF normalization via `.gitattributes` | Byte-identical canonical JSON hashes across OSes |
| D8 | Static local PDF copy under `.project-spec/` is git-ignored | Authoritative reference without committing a binary |
| D9 | No remote creation before review | Controlled delivery |
| D10 | No sibling access during implementation | Prevents strategy / state leakage |
| D11 | Both repositories created as PRIVATE under mohammedawad99 | Controlled academic delivery |
| D12 | Remote protocol is HTTPS (gh-authenticated) | Matches verified auth; no SSH keys or embedded tokens |
| D13 | Public visibility / lecturer access deferred | To be handled in a later reviewed stage |
| D14 | Branch protection / rulesets deferred | Until CI check names are known from the first run |
