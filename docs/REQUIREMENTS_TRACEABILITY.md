# Requirements Traceability Matrix - group MaRs-777

> **Status: DRAFT.** Seeded with approved **foundation** requirements only.
> The full extraction from book v3.0.0 (160 pages) is **pending**.

| Requirement ID | Requirement | Source | Mandatory/Optional | Repository | Component | Verification | Evidence | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| F-001 | Two separate police & thief repositories | Stage 0B directive | Mandatory | Both | Repo structure | `git rev-parse` in each; separate `.git` | Stage 0B report | Done | Independent repos |
| F-002 | Cross-link between the two repositories | Stage 0B directive | Mandatory | Both | README | README paired-repo section | README.md | Done | URLs marked future |
| F-003 | No secrets in Git history | Appendix E / SECURITY.md | Mandatory | Both | .gitignore, policy | Ignore patterns; no tracked secrets | .gitignore, SECURITY.md | Done | Zero commits so far |
| F-004 | Separate runtime state and processes | Stage 0B directive | Mandatory | Both | runtime/, process model | Per-repo runtime/ ignored; separate `.venv` | .gitignore, runtime/README.md | Partial | Enforced by structure |
| F-005 | Exact competition commit reproducible | Stage 0B directive | Mandatory | Both | VCS, uv.lock | Lockfile + future tag | uv.lock | Partial | Tagging pending |
| F-006 | Full requirements extraction from book v3.0.0 | Book v3.0.0 | Mandatory | Both | docs/ | Dedicated specification stage | - | Pending | 160 pages |
