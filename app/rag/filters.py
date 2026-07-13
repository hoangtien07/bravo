"""Small retrieval contracts with no database dependency."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalFilters:
    """Metadata constraints to be enforced inside retrieval SQL queries."""

    source_types: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    lifecycle_stages: tuple[str, ...] = ()

    @property
    def active(self) -> bool:
        return bool(self.source_types or self.modules or self.lifecycle_stages)
