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
