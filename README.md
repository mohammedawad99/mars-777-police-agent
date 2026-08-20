# mars-777-police-agent

**2026 Distributed Police-Thief Peer-to-Peer — Final Project**

- **Group code:** `MaRs-777`
- **Repository role:** **POLICE**
- **Companion repository:** **THIEF** — https://github.com/mohammedawad99/mars-777-thief-agent (private)
- **Status:** an autonomous agent. `uv run python -m mars777_police …` boots,
  serves its four FastMCP tools, reaches its opponent, plays a complete
  six-sub-game series and exits. It has also played six live sub-games against a
  third party's independent implementation. What it has **not** done is play a
  **counted** match against another group's agent.

This README is the user manual. Sections 1–3 say what the system is, 4–9 are the
operator manual, 10–14 are the engineering and programmatic surface, and 15–19
are the honest boundary of what is and is not done.

---

## 1. What the system is

Two teams each run two agents. A POLICE and a THIEF from **different** groups
meet over the public network, authenticate, negotiate and cryptographically lock
a shared configuration, then play a **series of exactly six sub-games** in
lockstep. Every action is committed before it is revealed, so neither side can
choose its move after seeing the other's. When the series ends, both sides hold
artifacts from which an auditor can re-derive the whole match.

### 1.1 Decision-process formulation (Dec-POMDP)

The match is modelled as a **decentralised partially-observable Markov decision
process** — two agents, no shared runtime state, each acting on its own partial
view.

| Element | This game |
|---|---|
| Agents `I` | `{police, thief}` — two processes, two repositories, no shared memory |
| States `S` | police cell, thief cell, the set of placed barriers, the police barrier quota consumed, the scent field, the move index within the sub-game, the sub-game index within the series, and the running score |
| Actions `A_i` | `N`, `S`, `E`, `W`, `STAY`. The **police** may additionally forgo its move to place one barrier (`BAR-004`), bounded by the negotiated quota |
| Transition `T` | **deterministic** given the acting agent's action; there is no environment noise. Agents alternate rather than act simultaneously, so on the other side's turn an agent's action is a no-op |
| Observations `Ω_i` | own cell; the public board, i.e. every placed barrier; own remaining barrier quota where the role has one; the scent emissions the opponent has **disclosed**; the opponent's hint sentence and its declared intent |
| Observation function `O` | **partial and asymmetric.** The opponent's cell is *never* observable. Scent is evidence about the environment the opponent passed through, not about where it is now |
| Reward `R` | the sub-game outcome — capture (police), survival (thief), timeout, or technical loss — scored by the negotiated scoring table and accumulated across the six sub-games |
| Horizon | finite: the negotiated step ceiling per sub-game (Appendix F minimum **35**), six sub-games per series |

The partial observability is the whole problem: the police must corner an
opponent whose position it cannot see, using only the terrain it can shape and
the traces the thief leaves behind.

### 1.2 Where the two repositories differ

Both repositories implement the same protocol, the same cryptography and the
same board. They differ only in **role**: which side they may play, which
actions are legal for them, and which strategy they compose. Neither imports the
other, and the environment cannot make this package boot as a thief.

---

## 2. Implementation status

Stated precisely, because "done" and "not done" are both misleading here.

### Implemented, covered by tests, and exercised in real processes

- **Game mechanics** — board, orthogonal movement, `STAY`, barrier placement and
  quota, capture, scoring, terminal conditions.
- **Protocol** — the state machine, per-transition evidence, the sub-game cursor,
  the delivery contract (apply / absorb / equivocation / buffer / violation /
  discard) and settlement that is **signalled, never inferred**.
- **Cryptography** — commit–reveal over SHA-256, sealed eight-member record,
  CSPRNG nonces, keyed Step-0 and configuration authentication, final nonce
  reveal, commitment recomputation, `TAMPERED` on mismatch, golden vectors.
- **Transport** — FastMCP over HTTP: four tools carrying nine frozen message
  kinds, strict DTOs, and **two envelope profiles** chosen before boot (see §10).
- **Autonomy** — the shipped CLI boots, connects, exchanges Step-0, plays
  `g01`…`g06` against a separate OS process, writes its fourteen official
  artifacts and exits 0.
- **Language and scent** — a deterministic hint channel (template catalogue,
  validator, zero tokens, no model, no network) and belief-level interpretation
  of the opponent's disclosed scent.
- **Strategy** — see §11.
- **Public network** — the group gateway and the tunnel adapter are wired behind
  one stable public route, with a ten-check readiness gate and proven teardown.
  **Demonstrated end to end**, including role handoff on a live public URL.
- **Third-party interoperability** — six live sub-games against the pinned
  interoperability kit, including the settlement divergence that exposed a real
  defect on our side (see `docs/DECISIONS.md`).
- **Replay Viewer** — a command that replays a finished sub-game from the
  artifacts alone and verifies every commitment (§6.4).
- **Graphical interface** — a live window showing local truth and the belief
  heatmap, and a replay window showing both agents and the verification result
  (§6.5). Both are read-only and neither is on the decision path.

### Not implemented

- a **counted match against another group's agent** — the runs above used either
  a synthetic distinct-group non-counted opponent or the interoperability kit in
  a friendly, explicitly non-counted mode;
- **Gmail result reporting**;
- **enforcement** of the negotiated rate limits — the terms are negotiated,
  validated and locked, but no component applies them at call time;
- the **systematic parameter study, analysis notebook and charts** — deliberately
  deferred to Stage 9B rather than fabricated.

The project is therefore neither "foundation only" nor "complete", and this
section is the authoritative boundary.

---

## 3. System requirements

| Requirement | Value |
|---|---|
| Python | **3.12** exactly (`.python-version`, `requires-python = "==3.12.*"`) |
| Package manager | **`uv`** — mandatory; `pip`, `venv` and `virtualenv` are not used |
| Operating system | Linux or Windows; CI proves both on every push |
| Network | outbound HTTPS for a real match; loopback only for local play |
| Tunnel (real match only) | an `ngrok` agent installed and authenticated **by the operator** |
| Disk | ~200 MB for the virtual environment; artifacts are a few hundred KB per series |

## 4. Installation

```bash
uv sync --frozen      # create .venv and install exactly what uv.lock pins
```

`--frozen` is the reproducible form: it refuses to silently re-resolve. Drop it
only when deliberately changing dependencies.

Verify the installation:

```bash
uv run pytest -q
```

## 5. Environment setup

Copy the committed template and fill it in locally:

```bash
cp .env.example .env
```

| Variable | Required | Meaning |
|---|---|---|
| `MARS777_ROLE` | yes | `police` for this repository. Boot refuses any other value |
| `MARS777_BIND_HOST` | yes | interface to listen on — loopback for local play |
| `MARS777_BIND_PORT` | yes | port to listen on |
| `MARS777_OPPONENT_ENDPOINT` | yes | the opponent's MCP URL |
| `MARS777_KEY_ID` | yes | names the pre-shared authentication key |
| `MARS777_AUTH_SECRET` | yes | the pre-shared secret itself. **Never committed**, never printed, never passed on the command line |
| `MARS777_ARTIFACT_ROOT` | yes | where this process writes **its own** official artifacts |
| `MARS777_RUN_LIVE_NGROK` | no | set to `1` to enable the live tunnel test suite |

The tunnel credential is **not** in this list on purpose: this project never
reads a tunnel token. It relies on the operator's own `ngrok` configuration, so
the credential never enters our process arguments, environment or logs.

## 6. Usage

### 6.1 Local strict series (two processes, one machine)

The internal wire, used for development and for the project's own artifacts:

```bash
# terminal 1 — the thief repository
uv run python -m mars777_thief --launch <launch.json>

# terminal 2 — this repository
uv run python -m mars777_police --launch <launch.json>
```

Each process serves, dials the other, exchanges Step-0, plays six sub-games,
writes fourteen artifacts and exits 0.

### 6.2 Interoperability (kit) mode

To speak the pinned third party's wire instead of ours, select the profile
**before boot** — it is never negotiated, because a wire cannot be agreed by the
messages whose encoding it governs:

```bash
uv run python -m mars777_police --launch <launch.json> --external-mode KIT_CORE_V1
```

### 6.3 Public match (role-split, one public URL)

A real match exposes **one** stable group URL that routes to whichever role is
playing the current sub-game:

```bash
# one backend per role, each in its own repository
uv run python -m mars777_police.kit_backend_main \
    --launch <doc> --port <private port> \
    --opponent <their public url> \
    --gateway-admin http://127.0.0.1:<admin port>/mcp \
    --first-role <police|thief>

# the group's public front door
uv run python -m mars777_police.kit_gateway_main \
    --police-endpoint <private> --thief-endpoint <private> \
    --ngrok <path to ngrok> --first-role <police|thief>
```

The full operator procedure, including what to check before and after the match,
is `docs/reference/MATCH_RUNBOOK.md`.

### 6.4 Replaying a finished game

Any grader or operator can replay a sub-game from the artifacts alone and see it
verified step by step:

```bash
uv run python -m mars777_police.replay_main \
    --log <log artifact> --config <config artifact> [--summary] [--step N]
```

Exit status `0` means every source-required commitment was present and matched,
`2` that the evidence could not be read, `3` that the replay **found** something
(a mismatch or an illegal step), and `4` that the audit is **incomplete** — a
commitment whose nonce was never disclosed. Absence is never reported as
tampering. Full guide: `docs/reference/REPLAY_VIEWER.md`.

### 6.5 Watching a match, and replaying one in a window

The same evidence, drawn instead of printed:

```bash
# step through a finished sub-game (arrow keys, Home, End)
uv run python -m mars777_police.gui_main replay \
    --log <log artifact> --config <config artifact>

# the same picture written to a file — needs no display at all
uv run python -m mars777_police.gui_main replay \
    --log <log> --config <config> --step 5 --png shot.png

# watch this agent play a counted series
uv run python -m mars777_police.gui_main live --launch <launch document>
```

`--png` needs no display and no window toolkit, so it works on any machine. The
interactive window needs `tkinter`, which Debian and Ubuntu package separately
(`sudo apt install python3-tk`); without it the command exits `2` with that
remedy rather than a traceback.

The live window shows **local truth only** — own cell, declared barriers, the
belief heatmap and its numbers, the received hint, and the turn-state banner. It
never shows the opponent's position, because the value it draws is projected
from the same `Observation` the strategy is restricted to and has no field one
could arrive in. The replay window may show both agents, because the audit point
has passed. Neither window has a control that reaches a decision. Full guide:
`docs/reference/GUI.md`.

### 6.6 Command-line options

| Option | Where | Meaning |
|---|---|---|
| `--launch` | all agent entrypoints | the series launch document: this side's opening configuration candidate and its identity |
| `--external-mode` | `mars777_police` | `STRICT_INTERNAL` (default) or the kit profile. Chosen pre-boot, never inferred |
| `--port` | `kit_backend_main` | this role's private backend port |
| `--opponent` | `kit_backend_main` | the counterparty's public URL |
| `--gateway-admin` | `kit_backend_main` | the gateway's admin endpoint, used to signal role handoff |
| `--first-role` | backend and gateway | which role plays sub-game 1; roles alternate thereafter |
| `--police-endpoint`, `--thief-endpoint` | `kit_gateway_main` | the two private backends the gateway routes between |
| `--ngrok` | `kit_gateway_main` | path to the operator's ngrok executable |
| `--evidence-root` | friendly runs | where development evidence is written |
| `--png` | `gui_main replay` | write the picture to a file instead of opening a window |

### 6.7 Exit status

| Code | Meaning |
|---|---|
| `0` | the series completed |
| `2` | local refusal — bad settings or an unreadable launch document |
| `4` | the opponent endpoint never became reachable |
| `5` | the peer refused us for a protocol reason; the frozen error identity is printed, never the payload |
| traceback | a genuine local defect. Deliberately not translated into a friendly code |

## 7. Configuration guide

There are two distinct configuration surfaces, and conflating them is a mistake:

**Negotiated game configuration.** Board geometry, movement set, barrier quota,
step ceiling, survival threshold, scent model, scoring, league terms and the
rate-limiter terms are **proposed, agreed with the peer and cryptographically
locked** at Step-0. They are not local settings and cannot be overridden at
runtime. Appendix F fixes which values are FIXED, which are MINIMUM floors and
which are NEGOTIABLE — for example a `7×7` minimum grid, a **14**-barrier
minimum quota, a **35**-move minimum ceiling, a `5×5` scent field, and exactly
**6** sub-games per series. Field-by-field detail:
`docs/spec/APPENDIX_F_NUMERIC_INVENTORY.md`.

**Local operator settings.** Everything in §5 — where to listen, whom to dial,
which key, where to write. These never cross the wire and are never hashed.

**Local provider limits.** `config/rate_limits.json` is the versioned policy the
API Gatekeeper enforces on calls to external **provider** services: requests per
minute and per hour, concurrent calls, waiting-room depth, retry budget, backoff
and which HTTP statuses may be repeated. Its `rate_limits.version` is validated
at load, and an unsupported version refuses rather than falling back. It is
**ours alone** — it is not negotiated, not hashed, and not the peer's
`rate_limiter_gatekeeper` terms, which are an Appendix-F floor agreed with the
opponent. It contains no secret. Peer gameplay calls are deliberately **not**
governed by it: repeating a turn the opponent has already applied would be a
protocol violation, so they keep their own delivery, ordering and timeout
authorities.

The launch document passed to `--launch` carries this side's *opening candidate*
for the negotiated configuration. It is decoded by the same codec the wire uses,
so there is no second configuration schema.

## 8. Testing and quality

```bash
uv run python tools/check_python_loc.py   # every file <= 150 code lines
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov --cov-report=term-missing
uv build
```

The first command is the file-size gate. It counts code lines the way the
professional-software guideline defines them - blank lines and comment-only
lines excluded, docstrings counted - across **`src/` and `tests/` alike**, and
it is the same command CI runs, so a size failure is never a surprise at push
time.

The coverage gate is `fail_under = 90` in `pyproject.toml`; the suite currently
measures **100%**. CI runs all of the above on Ubuntu and Windows for every push.
Thirteen tests are skipped unless `MARS777_RUN_LIVE_NGROK=1`: they need a real
tunnel and would otherwise fail for an environmental reason rather than a code
one.

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `cannot start: MARS777_ROLE contradicts this repository's role` | the police package was started with `thief` | this repository can only be the police; use the sibling repository |
| `cannot start: …` naming a variable | a required environment variable is missing or malformed | the message names the **variable**, never the value; set it in `.env` |
| exit `4` | the opponent was not listening within the startup budget | start the other side first, or check the endpoint and the tunnel |
| exit `5` with an error identity | the peer refused us for a protocol reason | look the identity up in `docs/architecture/ERROR_MODEL.md` |
| the live ngrok tests all skip | `MARS777_RUN_LIVE_NGROK` is unset | that is the intended default; set it to `1` only with a real tunnel |
| `uv sync` wants to re-resolve | the lock and the manifest disagree | run `uv sync --frozen` and fix the manifest deliberately, never by re-resolving silently |
| a settled result disagrees with the peer's | a genuine protocol or rules divergence | do **not** patch the symptom; the settlement divergence of Stage 8A-2R is the worked example in `docs/DECISIONS.md` |

## 10. FastMCP — how the two agents actually talk

The agents communicate over **FastMCP** (Model Context Protocol) carried on
HTTP. Each agent runs an MCP server exposing exactly four tools, and an MCP
client that calls the opponent's:

| Tool | Message kinds it carries |
|---|---|
| `negotiate` | `step0`, `config_proposal`, `config_lock` — identity, keyed authentication and the configuration agreement |
| `receive_turn` | `commitment`, `acknowledgement`, `reveal` — one turn, with its hint and scent emission |
| `submit_audit` | `final_nonce_reveal`, `audit_disclosure` |
| `receive_control` | `result_agreement` |

Four tools, **nine kinds**, no heartbeat and no alias: the matrix is frozen in
`transport/envelopes.py`, and a kind sent to the wrong tool is refused rather
than tolerated.

Two **envelope profiles** exist over those four tools — the project's strict
internal wire and the pinned third-party kit's wire. The profile is selected
before boot and is never auto-detected or downgraded. Framework imports are
confined to the `transport` package, and a test refuses any FastMCP import that
tries to escape it, so the game logic never depends on the framework.
Architecture: `docs/architecture/API_BOUNDARIES.md`.

## 11. Strategies

Three strategy artefacts exist behind one `StrategyPort`, so swapping them
changes no other code.

**`BaselineStrategy` (Stage 6B, extended 7C) — the frozen reference.** From own
position, the public board and the locked quota it chooses a legal deterministic
action by an accessibility objective: prefer the action that best improves the
police's reachable share of the board relative to where the thief could be.
Since Stage 7C, when that objective **ties**, the belief folded from the
opponent's own disclosed scent emissions breaks the tie. No opponent position,
no LLM, no randomness.

**`CompetitiveStrategy` (Stage 7D-B) — what this repository actually ships.**
It keeps the baseline's move and displaces it with a lawful barrier placement
only when the scent evidence supporting the barrier cell is *strictly* stronger
than the evidence where the baseline would have moved. It never declares a
capture: a barrier that misses costs one turn, while a wrong capture claim
forfeits the sub-game. It is **PROJECT-DERIVED** — Ch 6 §6.3.1 leaves the
movement policy to the group — and was promoted on a development, non-counted
benchmark (0 → 12 captures over 140 deterministic scenarios). It is not Bayes,
not reinforcement learning, and not a claim of optimality.

**Deliberately absent.** No learning of any kind is implemented, so **no
learning curve is presented**. Producing one would require the systematic
parameter study that is scheduled for Stage 9B; inventing one now would be a
fabricated result.

## 12. Screenshots and demonstrations

Both pictures below were produced by the **real** renderer from **one**
thirty-five-round sub-game two composed agents actually played in this
repository. Neither is drawn, mocked, or a diagram of an application, and
neither shows a secret, a token or a private path.

### The live window — local truth and the belief heatmap

![Live window showing this agent's own cell, a belief heatmap with per-cell
values, the turn-state banner, and the statement that the opponent position is
never shown](docs/evidence/gui/live_belief_map.png)

`GUI-001` and `GUI-003`. Own cell (`ME`), the folded belief map with every
heated cell carrying its own number, the barrier quota, the last action, the
received hint, and the two statements that make the limit explicit —
`belief (estimate) - not a sighting` and `opponent position: never shown`. There
is no opponent cell on this screen because the value it is drawn from has no
field one could arrive in (`GUI-002`).

### The replay window — verification of the same sub-game

![Replay window showing both agents' true cells, Verified OK for both sides with
an OK glyph, a CONSISTENT semantic verdict, and audit complete
yes](docs/evidence/gui/replay_verified.png)

`REPLAY-001`, `REPLAY-002` and `PRD07-FR-023`. **After** the audit point, and
only then, both agents' true cells may be shown. Every verification word carries
a glyph as well as a colour, so `Verified OK`, `TAMPERED` and `NOT_CHECKABLE`
stay distinguishable without colour.

The identities in both pictures (`MaRs-777-vs-GROUP-XY`) are **development
identities**. This was not a tournament match and is not presented as one.

Regenerate both from a fresh run:

```bash
MARS777_WRITE_GUI_EVIDENCE=1 uv run pytest tests/gui/test_gui_evidence.py
```

## 13. Programmatic use — the SDK

Everything this agent can do is reachable from one import path. The command
lines shipped here use it, and so would a graphical interface, a replay viewer,
or any third party who installed the distribution.

```python
import asyncio
from pathlib import Path

from mars777_police.sdk import AgentSdk, StrictSeriesRequest

sdk = AgentSdk()  # verifies this installation is this source
artifacts = asyncio.run(sdk.run_strict_series(StrictSeriesRequest(launch=Path("launch.json"))))
```

| Operation | What it does |
|---|---|
| `run_strict_series(request)` | plays one complete series and returns where the artifacts were written |
| `compose_role_backend(request)` | assembles this role's friendly backend; nothing is served or dialled |
| `write_contribution(backend, root)` | writes a finished backend's development evidence and says where |
| `compose_public_gateway(request)` | assembles the group's public front door; no route is opened yet |
| `verify_config_artifact(document)` | returns what a stored config artifact proves, or refuses it |
| `open_replay(log, config, root)` | returns a navigable, already-verified replay of one finished sub-game |
| `verify_replay(log, config, root)` | returns that replay's summary alone, for a caller that only wants the verdict |

The requests (`StrictSeriesRequest`, `RoleBackendRequest`, `PublicGatewayRequest`)
and the failures a caller must tell apart (`SettingsError`, `LaunchInputError`,
`TransportFailureError`, `PeerProtocolError`, `LocalDefectError`,
`PublicIngressError`, `SoftwareVersionError`) are exported from the same place.
The names in `mars777_police.sdk.__all__` are the promise; anything else in the
package is an implementation detail.

**What the SDK is not.** It holds no game rules, no cryptography, no strategy, no
transport and no provider mechanics — it forwards to the layers that own them.

**The live view is a seam, not a screen.** `LiveViewSink`, `LatestSnapshot` and
`LiveViewSnapshot` are exported so a viewer can attach to a running series and
name what it receives; pass one as `StrictSeriesRequest(..., viewer=...)` and
every turn's lawful local view is published to it. The drawing itself lives in
`mars777_police.gui`, which *consumes* this facade — a presentation package
imported by the facade would point the dependency the wrong way, and would make
every command line load an imaging library in order to parse an argument.

**Software version.** `mars777_police.sdk.SOFTWARE_VERSION` is the single
authority. It renders two ways — `1.00`, the professional-software guideline's
literal, and `1.0`, the packaging form declared in `pyproject.toml` — from one
stored value, so the two cannot drift.

## 14. Documentation map

| Document | What it is for |
|---|---|
| `docs/PRD.md` + `docs/prd/PRD-01…07` | what the product must do, per mechanism |
| `docs/PLAN.md` | the architecture and the stage-by-stage plan, with current status |
| `docs/TODO.md` | the remaining task list |
| `docs/DECISIONS.md` | every decision the sources did not make for us, with its rationale |
| `docs/AI_WORKFLOW.md`, `docs/PROMPTS.md` | how this project was built with AI assistance, and the prompt log |
| `docs/architecture/` | 21 architecture documents — boundaries, dependency rules, state, security, concurrency, quality gates |
| `docs/spec/` | the book extraction: requirement catalog, appendix crosswalks, numeric inventory, conflict register |
| `docs/reference/MATCH_RUNBOOK.md` | the operator procedure for a real match |
| `docs/reference/REPLAY_VIEWER.md` | how to replay and verify a finished game log |
| `docs/reference/GUI.md` | the live and replay windows: what they may show, and why they cannot affect a match |
| `docs/GUIDELINE_ALIGNMENT.md` | alignment with the professional-software excellence guideline |
| `docs/COSTS.md` | measured resource use |
| `docs/SUBMISSION_CHECKLIST.md` | what still gates delivery |

## 15. Contributing

- **Workflow:** requirement → PRD → PLAN → TODO → implement → verify → review →
  commit → push. Nothing is implemented before an approved plan, and nothing is
  committed or pushed without an explicit instruction.
- **Tests first.** Every implementation stage in this repository was written
  test-first; that is the recorded method, not an aspiration.
- **Style:** ruff (lint **and** format) with zero violations, `mypy --strict`,
  and **no source file over 150 code lines** — split, never compress.
- **Docstrings explain *why*.** A module docstring that only restates the class
  name is not documentation.
- **Never** import the sibling repository, copy its strategy, change
  `GROUP_CODE`, vendor the interoperability kit, or weaken authentication.

Full contributor guidance: `CONTRIBUTING.md`.

## 16. Security

Never commit credentials, tokens, OAuth files, private keys or tunnel
configuration. Secrets come from the environment only; the authentication secret
is wrapped in a type whose `repr` and `str` render `<withheld>`, so it cannot
leak into a log line or a traceback. If a secret is ever exposed, revoke it
immediately. Policy: `SECURITY.md`. Threat model:
`docs/architecture/SECURITY_ARCHITECTURE.md`.

## 17. Isolation statement

This POLICE agent shares **no live state** with the opposing THIEF agent:
separate repository, separate `.venv`, separate process, separate configuration,
logs and runtime state. There is no shared package, database, cache or memory.

## 18. License and credits

**License: proprietary / unlicensed academic coursework.** This repository is
submitted for assessment in the 2026 Distributed Police-Thief course. No licence
to use, copy, modify or distribute it is granted, which is what
`license = { text = "UNLICENSED" }` in `pyproject.toml` records. No open-source
licence has been chosen, and none is implied.

**Authors.** Group `MaRs-777`. GitHub owner **mohammedawad99**; collaborator
**Rawey7** — access pending explicit instruction. Development was AI-assisted
under human supervision; the method and its corrections are recorded in
`docs/AI_WORKFLOW.md` and `docs/PROMPTS.md`.

**Third-party components.**

| Component | Version | Licence | Use |
|---|---|---|---|
| `fastmcp` | 3.4.6 | Apache-2.0 | MCP server and client transport |
| `pydantic` | 2.13.4 | MIT | strict wire DTO validation |
| `pytest`, `pytest-cov`, `ruff`, `mypy` | see `uv.lock` | MIT | development and quality gates |
| `uv` | external tool | Apache-2.0 OR MIT | package management and task running |
| `ngrok` agent | operator-installed | proprietary, operator's own account | public ingress for a real match |
| `Imreec/copthief-league-protocol` @ `ad655762` | pinned commit | see that repository | **interoperability reference only** — read, never vendored into this repository and never modified |

**Sources.** The project book v3.0.0 and the course materials are the property of
their authors and are **not** redistributed here; the book is read from a local,
git-ignored path. See `docs/SOURCES.md`.

## 19. Known limitations

1. No counted match against another group's agent has been played.
2. No Gmail reporting. The Replay Viewer exists as of Stage 9A-2A and the
   graphical interface as of Stage 9A-2B, so the `DOC-001` screenshot component
   is closed (§12); the reporting component is not.
3. The Gmail reporting rate-limiter the book requires (`REPORT-003`) has no
   surface yet: the Gatekeeper exists and is proven, but there is no sender.
4. No parameter study, notebook or charts yet (Stage 9B).
5. Thirteen tunnel tests require a real ngrok agent and are skipped by default.
6. One documented Windows-native limitation is isolated in its own CI job so it
   stays visible rather than being hidden by a skip.
7. The version authority covers this **software** only. There is no
   `rate_limits.version` and no local versioned configuration file yet; the
   binding game configuration is negotiated and locked with the peer instead
   (`docs/GUIDELINE_ALIGNMENT.md` §8.1).
