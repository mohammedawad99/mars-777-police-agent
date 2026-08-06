# config/

**Status: DRAFT (foundation).**

This directory is **tracked**. It will hold the future **shared, signed game
configuration** negotiated for a competition game. That configuration must be
reproducible and version-controlled.

- Do **not** place secrets here (tokens, keys, OAuth files). Those are ignored
  by `.gitignore` and stay under `runtime/` or a local `.env` file.
- Signed configuration files added here must be reviewed before commit.

No real configuration exists yet.
