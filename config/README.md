# config/

**Status: CURRENT.**

This directory is **tracked**, and it holds two different kinds of thing. Keeping
them apart matters more than keeping them together.

## 1. `rate_limits.json` — local provider limits (present)

The versioned local configuration for the API Gatekeeper: how fast, how many at
once, how deep the waiting room, and how a provider failure may be retried. It
is **ours alone** - no peer sees it, agrees to it, or is bound by it, and it
never reaches `config_sha256`, Step-0, the KIT wire or any artifact.

Its `rate_limits.version` is a **string** (`"1.00"`): written as a JSON number it
would read back as `1.0`, which is a second truth about one value.

**When the version rises.** It guards *representability*, so it is raised only
when an existing valid document would stop being valid or would change meaning -
a key removed, a key renamed, a value reinterpreted. Adding a **service entry**
is data. Adding an **optional key whose default reproduces the previous
behaviour exactly** is a compatible extension. The admission keys added at Stage
9A-2C are the second kind, so `1.00` still describes every document this build
accepts. The rule itself lives in `shared/rate_limits.py`.

### Services

| Service | Admission | Why |
|---|---|---|
| `default` | rolling windows | Appendix F Table 19 example values, which its MINIMUM status makes the required defaults |
| `ngrok.discover_tunnels` | rolling windows | a loopback readiness poll, deliberately faster and never retried |
| `gmail.send_report` | **token bucket** + daily quota + DOS detector | Appendix E rule 28 names the algorithm, and Ch 9 §9.3.1 names all three mechanisms. See `docs/reference/REPORTING.md` §6-§7 |

## 2. The shared, signed game configuration (future)

The negotiated physics and scoring contract - board, movement, barriers, scent,
scoring, league terms and the peer-agreed `rate_limiter_gatekeeper` floors - is
**not** a file in this directory. It is proposed, agreed with the opponent and
cryptographically locked at Step-0, and it lives in `NegotiatedConfig`. If a
signed configuration file is ever committed here, it must be reviewed first.

**Local provider limits are not negotiated peer limits.** The first is
operational policy this repository chooses; the second is an Appendix-F floor an
opponent agreed to. Nothing in this directory may blur that.

- Do **not** place secrets here (tokens, keys, OAuth files). Those are ignored by
  `.gitignore` and stay in the operator's own environment or agent configuration.
