"""Data layer (Phase 2) — financial numbers. Principle: LLM CHOOSES, engine COMPUTES.

- semantic.py : metric/semantic layer (ADR-0005) — LLM maps NL -> (metric, dimension,
                filter); engine generates deterministic SQL. NO free-form SQL.
- calc.py     : deterministic derived calc in a sandbox (ADR-0004, PAL/PoT). LLM never
                emits final numbers.
- grounding.py: abstain/verify gate (findings/H) — every number traces to a source;
                refuse when out-of-scope / low confidence.
"""
