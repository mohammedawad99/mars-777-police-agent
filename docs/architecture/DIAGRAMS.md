# Architecture diagrams — group MaRs-777

**Mermaid source, committed as text.** Diagrams live beside the code they
describe so they can be reviewed in a diff and corrected in a pull request. No
diagram tool is added to the runtime dependencies: GitHub, VS Code and most
Markdown viewers render these blocks directly, and nothing here needs a build
step.

**Every element below exists in this repository today.** No planned service, no
aspirational component, no box that is really a wish. Where something is
partner-dependent or operator-authorised it is drawn with a dashed edge and
labelled as such, so an unperformed step is never mistaken for a shipped one.

---

## 1. System / container view

One group, one public URL, two independent role processes. The Police and Thief
agents are **separate repositories and separate processes**; they never import
each other and never share state.

```mermaid
flowchart TB
    operator([Operator])

    subgraph public["Public ingress (per run, never committed)"]
        tunnel["Provider tunnel<br/>one stable group URL"]
    end

    subgraph group["Group MaRs-777"]
        gateway["Gateway process<br/>kit_gateway_main<br/><i>routes only, plays nothing</i>"]
        police["POLICE agent process<br/>mars777-agent / mars777-backend<br/><i>this repository</i>"]
        thief["THIEF agent process<br/>sibling repository<br/><i>independent package</i>"]
    end

    peer([Opponent group agent<br/>external, unknown implementation])
    gmail[["Gmail API<br/>send-only scope"]]
    store[("Artifact output root<br/>MARS777_ARTIFACT_ROOT<br/>14 official files per counted series")]

    operator -->|"launch document, env"| gateway
    operator -->|"launch document, env"| police
    gateway --- tunnel
    tunnel <-.->|"FastMCP over HTTP<br/>negotiate · receive_turn<br/>submit_audit · receive_control"| peer
    gateway -->|"private local port"| police
    gateway -->|"private local port"| thief
    police --> store
    thief --> store
    police -.->|"result JSON attachment<br/><b>operator-authorised</b>"| gmail

    classDef ext fill:#eef2ff,stroke:#4d7fff;
    classDef pending stroke-dasharray: 5 5;
    class peer,gmail ext;
    class gmail pending;
```

**Read the dashes.** The opponent edge is exercised against a pinned third-party
kit and against our own public loopback; a **counted** match against another
group's agent has not happened and is partner-dependent. The Gmail edge is
implemented and tested end to end against a fake transport, but **no live send
has been performed** — that needs explicit operator authorisation.

---

## 2. Application component view

Dependencies point inward only. `domain` knows nothing of `app`; `app` reaches
outward exclusively through ports; `research` is evidence and is **not** part of
the distributed package.

```mermaid
flowchart TB
    subgraph transport["transport · public network"]
        fastmcp["FastMCP server + client"]
        wire["wire codecs<br/>envelope profiles"]
        gw["gateway + role routing"]
    end

    subgraph app["app — orchestration, protocol, policy"]
        proto["protocol runtimes<br/>step0 · negotiation · lock · turn · result"]
        strat["CompetitiveStrategy<br/><i>promoted barrier rule</i>"]
        audit["audit + semantic replay<br/>Gate 1 · Gate 2"]
        report["reporting + Gatekeeper<br/>token bucket · quota · DOS"]
        artifacts["artifact writers"]
    end

    subgraph domain["domain — pure rules, no I/O"]
        board["board · movement · barriers"]
        scent["scent model · belief"]
        scoring["terminal · scoring"]
    end

    sdk["sdk — public typed façade"]
    gui["gui — live + replay windows<br/><i>observes, never decides</i>"]
    research["research/ — benchmark + candidates<br/><i>not packaged, never imported by src/</i>"]

    transport --> app
    app --> domain
    sdk --> app
    gui -.->|"read-only snapshot"| app
    research -.->|"imports production, never the reverse"| app

    classDef pure fill:#f6fff6,stroke:#3a7;
    classDef outside fill:#fff8f0,stroke:#c96,stroke-dasharray: 5 5;
    class domain,board,scent,scoring pure;
    class research outside;
```

The two dashed edges are the ones a reviewer should check: the GUI may **read** a
turn snapshot and may never decide anything, and `research` depends on production
while production never depends on `research` — asserted by a test that parses
every production module's imports.

---

## 3. Counted sub-game sequence

One lawful sub-game, from config negotiation to a report that is ready to send.
Both sides seal before either reveals; that ordering is what the audit checks.

```mermaid
sequenceDiagram
    autonumber
    participant P as Police agent
    participant T as Opponent agent
    participant A as Audit + semantic replay
    participant R as Artifacts / report

    Note over P,T: Step-0 — identity, capability inventory, keyed proof
    P->>T: negotiate(step0 inventory + HMAC proof)
    T-->>P: step0 inventory + proof
    Note over P,T: both verify; a failed proof is E-AUTH-FAILURE, no fallback

    P->>T: negotiate(config proposal)
    T-->>P: config proposal / acceptance
    P->>T: negotiate(config lock + config_sha256)
    T-->>P: lock evidence
    Note over P,T: CONFIG_LOCKED — 35 members, digest agreed both ways

    loop each step until a terminal
        P->>P: Observation → strategy → action
        P->>T: receive_turn(commitment = H(payload ‖ nonce))
        T-->>P: acknowledgement
        P->>T: receive_turn(reveal: move, hint, scent emission)
        T-->>P: reveal
        Note over P,T: sealed before revealed — neither saw the other's step
        P->>P: adopt peer effects, answer capture truthfully
    end

    P->>T: submit_audit(final nonce reveal)
    T-->>P: final nonce reveal
    P->>A: disclosed transcript + config + nonces
    A-->>P: Gate 1 commitments VERIFIED
    A-->>P: Gate 2 semantic verdict CONSISTENT
    P->>T: receive_control(result agreement + result_sha256)
    T-->>P: digest response
    P->>R: 14 official artifacts written
    R-->>P: result_<game_id>.json ready
    Note over R: Gmail send is operator-authorised and has not been performed
```

---

## 4. Deployment / public ingress

**One public URL for the group, not one per role.** The gateway is the only
thing the partner addresses; role selection happens behind it.

```mermaid
flowchart LR
    peer([Opponent group]) -->|"https://<one group URL>/mcp"| tunnel

    subgraph host["Operator machine"]
        tunnel["Provider tunnel client<br/><i>URL discovered per run</i>"]
        gateway["Gateway<br/>public route + loopback admin"]
        police["Police backend<br/>127.0.0.1:&lt;private&gt;"]
        thief["Thief backend<br/>127.0.0.1:&lt;private&gt;"]
    end

    tunnel --> gateway
    gateway -->|"role routing<br/>odd/even alternation"| police
    gateway -->|"role routing"| thief

    note["Private ports are configuration.<br/>They are never advertised, never committed,<br/>and no hostname is remembered between runs."]
    gateway -.- note

    classDef quiet fill:#fafafa,stroke:#bbb,color:#555;
    class note quiet;
```

---

## Keeping these true

Each diagram names real modules (`kit_gateway_main`, `CompetitiveStrategy`,
`semantic_replay`) and real tool names (`negotiate`, `receive_turn`,
`submit_audit`, `receive_control`). If one of those disappears, the diagram is
wrong and should fail review — that is the reason for naming them rather than
drawing generic boxes.
