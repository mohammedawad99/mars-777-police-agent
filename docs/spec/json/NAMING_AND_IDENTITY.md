# Naming & Identity Contract — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Source-backed rules for artifact filenames and identifiers. Sources: App F Table
20 (PDF p.157), Ch 9 §9.3.3 (PDF p.95), App F §2.3 (PDF p.156), App E #53 / Ch 5
§5.5 (commit hash), App E #45 (group id).

## Filenames (SOURCE-EXPLICIT — never rename)

| Artifact | Filename pattern | Provenance | Source |
|---|---|---|---|
| declaration | `declaration_<game_id>.json` | **SOURCE-EXPLICIT** | App F Tbl 20 p.157 |
| config | `config_<game_id>_g<NN>.json` | **SOURCE-EXPLICIT** | App F Tbl 20 p.157 |
| log | `log_<game_id>_g<NN>.json` | **SOURCE-EXPLICIT** | App F Tbl 20 p.157 |
| result | `result_<game_id>.json` | **SOURCE-EXPLICIT** | App F Tbl 20 p.157 |

Rule (SOURCE-EXPLICIT): names derive from `game_id`; the two per-sub-game files add
`g<NN>`; different games must never share names, so files never mix between games
(App F §2.3, Ch 9 p.95).

## Identifiers

| Identifier | Provenance | Rule | Source |
|---|---|---|---|
| `game_id` | **SOURCE-EXPLICIT** (named Ch 9 p.95: filename-derivation id); **PROJECT-CONTRACT** format only | see JDEC-005 | App F Tbl 20; Ch 9 p.95 |
| `game_uid` | **SOURCE-EXPLICIT** (named Ch 9 p.95: "the four files carry a shared identifier `game_uid`"); **PROJECT-CONTRACT** format only | shared across the 4 files | Ch 9 p.95 |
| `<NN>` sub-game index | SOURCE-SEMANTIC (a sub-game number exists) + **PROJECT-CONTRACT** width | see JDEC-004 | App F Tbl 20; Ch 5 p.55 |
| `group_id` | **SOURCE-EXPLICIT** rule (8 chars, no spaces) | exactly 8 chars, no spaces; `MaRs-777` ✓ | App E #45 (SUB-003) |
| `github_commit` | **SOURCE-EXPLICIT** field | the exact commit hash played, updated per game | App E #53; Ch 5 p.56 (GIT-003) |

## `<NN>` zero-padding — NOT source-specified

The book writes the placeholder `g<NN>` (App F Tbl 20) but **does not state a
zero-padding width**. We therefore do **not** claim a width is source-mandated. A
project convention is selected: **`<NN>` is two digits, zero-padded** (`g01`…`g06`
for the 6-sub-game series). This is **PROJECT-CONTRACT** → **JDEC-004**. Rationale:
lexicographic sort matches numeric order; 6 (and the ≤10 max) fit two digits.

## `game_id` / `game_uid` — source-named; only the format is project (D3)

**Both `game_id` and `game_uid` are named by the book** (Ch 9 p.95): `game_uid` is
the shared identifier the four files carry; `game_id` is the identifier from which
filenames derive. Stage 1D **refutes** the idea that `game_uid` was a Stage-1C
invention — it is SOURCE-EXPLICIT and is **kept**. The book does **not** fix their
internal **format**, so only the format is **PROJECT-CONTRACT** (**JDEC-005**):
each is an opaque, filesystem-safe, collision-resistant `[a-z0-9-]` string;
`game_uid` is the short shared token embedded in all four files; `game_id` (used in
filenames) may embed `game_uid` (e.g., `<a>-vs-<b>-<yyyyww>-<game_uid>`). Neither
is claimed lecturer-specified beyond the names themselves. INV-01 binds all four
files to the same `game_id` **and** `game_uid` so filename and JSON identity cannot
drift.

## Uniqueness / non-mixing invariants

- All four files of one game carry the **same** `game_id` and `game_uid` (INV-01).
- `config`/`log` for the same sub-game carry the **same** `<NN>` (INV-02).
- Each game's config is attached to the repo under its unique name (App F §2.4).

(See `CROSS_ARTIFACT_INVARIANTS.md`.)
