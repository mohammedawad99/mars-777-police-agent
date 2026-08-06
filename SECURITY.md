# Security Policy - group MaRs-777

## Secret handling

- **Never** commit or report real credentials, tokens, API keys, OAuth client
  secrets, private keys, or tunnel tokens.
- If a secret is ever exposed (committed, printed, or shared), **revoke and
  rotate it immediately**, then purge it from history before any push.
- Runtime and OAuth secrets remain **local only** and are covered by
  `.gitignore` (`.env`, `credentials.json`, `token.json`, `*.pem`, `*.key`,
  `client_secret*.json`, `ngrok.yml`).
- **Tunnel tokens are never versioned.**
- Runtime **logs must be reviewed** before any promotion to tracked evidence
  under `artifacts/`, to ensure they contain no secrets or opponent-private data.
- **Security reports must not contain real tokens** - redact before sharing.

## Reporting

Report suspected exposure privately to the repository owner
(**mohammedawad99**). Do not open a public issue containing sensitive detail.

## Scope

This is a foundation-stage repository; no networking, cryptography, or runtime
secret handling is implemented yet. This policy governs all future work.
