# Frozen A/B baseline artifacts

Create one new directory per synthetic baseline run with
`python -m app.eval.frozen_ab_baseline`. A directory must contain `baseline.json` and
`SHA256SUMS`; the command refuses to overwrite it.

The replay input must be created by `app.eval.consultant_replay` with `--persist-answers` against
the frozen synthetic fixture. Record only hashes for prompts and evidence snapshots. Never place a
credential, raw `.env` value, customer input, or live production trace in this directory.

Commit the completed synthetic artifact before changing prompt, routing, retrieval, or synthesis.
