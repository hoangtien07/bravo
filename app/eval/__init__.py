"""Evaluation harness (Phase 1E) — the quality gate (findings/J).

- probes.py : cross-tenant ACL leak probes (RLS regression — catches the Slack/Sage
              failure class). MUST stay green; a leak is a release blocker.
- golden.py : golden Q&A schema (citation accuracy, refusal correctness).
- run.py    : CI runner. Tách metric retriever (recall/leak) vs generator (faithfulness).
"""
