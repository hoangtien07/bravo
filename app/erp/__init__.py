"""ERP integration (Phase 2) — NON-INVASIVE (VISION §2).

- client.py     : READ-ONLY REST client to BRAVO ERP, via approved views/metrics only.
- draft_queue.py: AI writes go to a DRAFT queue for human approval on the ERP UI;
                  never a direct write to the ERP SQL Server.
"""
