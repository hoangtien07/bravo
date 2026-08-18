# WP19-01 owner fixture acceptance

- **Decision date:** 2026-08-18
- **Decision:** The project owner accepted the synthetic Knowledge Chat V2 ten-transaction fixture
  under the `tt99/2025` chart-of-accounts policy and accepted ADR-0034.
- **Scope:** The acceptance covers only the checked-in synthetic fixture pack and the proposed
  framework-independent Conversation Core V2 boundary. It does not authorize ERP mutation, use of
  customer data, prompt/model migration, retrieval changes, or a production claim.
- **Remaining gate:** Independent accounting and BRAVO SME review is still required before a
  deterministic accounting engine or substantive Conversation Core V2 implementation starts.

The fixture is integrity-bound through its local manifest and SHA-256 checksum list. This record
does not convert owner acceptance into blind-SME or quality evidence.
