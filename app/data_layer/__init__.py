"""Data layer (Phase 2) — financial numbers. Principle: LLM CHOOSES, engine COMPUTES.

- semantic.py : metric/semantic layer (ADR-0005) — LLM maps NL -> (metric, dimension,
                filter); engine generates deterministic SQL. NO free-form SQL.
- calc.py     : deterministic derived calc in a sandbox (ADR-0004, PAL/PoT). LLM never
                emits final numbers.
- grounding.py: abstain/verify gate (findings/H) — every number traces to a source;
                refuse when out-of-scope / low confidence.

Importing this package NẠP whitelist metric (register_catalog) như side-effect, để MỌI
entrypoint chạm data_layer (API/eval/script) đều có REGISTRY đầy đủ — không còn cảnh
catalog rỗng lúc runtime khiến metric_lookup abstain 100%. register() là idempotent.
"""

from app.data_layer import catalog as _catalog  # noqa: F401,E402 — side-effect: register_catalog()
