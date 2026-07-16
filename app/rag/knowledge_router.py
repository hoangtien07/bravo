"""Deterministic, auditable corpus routing for BRAVO knowledge retrieval.

The router deliberately runs before retrieval.  It converts the existing lifecycle playbooks
and BRAVO intent hints into SQL-level metadata constraints so a user-guide question does not
start by competing with every technical and BA document in the corpus.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agent.bravo_playbooks import BravoPlaybook, select_playbooks
from app.rag.bravo_intent import BravoQueryIntent, infer_query_intent
from app.rag.filters import RetrievalFilters


def _unique(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


@dataclass(frozen=True)
class KnowledgeRoute:
    """A retrieval decision that is safe to log, test and expose in an agent trace."""

    source_types: tuple[str, ...]
    modules: tuple[str, ...]
    lifecycle_stage: str | None
    playbook_modes: tuple[str, ...]
    reason: str

    @property
    def filters(self) -> RetrievalFilters:
        # Source type is the hard scope selected by the lifecycle playbook.  Module is a
        # secondary precision filter only when intent identifies one module; lifecycle metadata
        # is informative but not required because many legacy chunks do not carry it.
        return RetrievalFilters(source_types=self.source_types, modules=self.modules)

    @property
    def is_scoped(self) -> bool:
        return bool(self.source_types or self.modules)


def _from_playbooks(intent: BravoQueryIntent, playbooks: tuple[BravoPlaybook, ...]) -> KnowledgeRoute:
    source_types: list[str] = []
    for playbook in playbooks:
        source_types.extend(playbook.preferred_source_types)

    # The playbook is the product-owned authority.  When a playbook matches, do not append every
    # loose keyword hint (for example a how-to report question must stay in user guides instead
    # of reopening technical manuals merely because it contains the word "báo cáo").
    return KnowledgeRoute(
        source_types=_unique(source_types),
        modules=intent.modules,
        lifecycle_stage=playbooks[0].lifecycle_stage if playbooks else intent.lifecycle_stage,
        playbook_modes=tuple(playbook.mode for playbook in playbooks),
        reason="playbook",
    )


def route_query(query: str) -> KnowledgeRoute:
    """Choose an initial corpus scope without an LLM or post-retrieval score hack.

    If no lifecycle playbook applies, deterministic BRAVO intent remains useful and is used as a
    conservative fallback.  A fully unknown question stays unscoped so the existing general RAG
    behavior remains available instead of returning a false zero-hit.
    """
    intent = infer_query_intent(query)
    try:
        playbooks = select_playbooks(query)
    except Exception:
        playbooks = ()
    if playbooks:
        # `select_playbooks()` intentionally returns two prompt hints. Retrieval needs a single
        # primary scope; unioning both reintroduces the broad-search failure this router fixes.
        primary = next(
            (playbook for playbook in playbooks
             if intent.lifecycle_stage and playbook.lifecycle_stage == intent.lifecycle_stage),
            playbooks[0],
        )
        return _from_playbooks(intent, (primary,))
    return KnowledgeRoute(
        source_types=intent.source_types,
        modules=intent.modules,
        lifecycle_stage=intent.lifecycle_stage,
        playbook_modes=(),
        reason="intent" if intent.has_hints else "unscoped",
    )


_PROFILE_ROUTES: dict[str, tuple[tuple[str, ...], str, tuple[str, ...]]] = {
    # Product profiles are policy bundles: they narrow the source surface before retrieval.
    # They are not model selectors and cannot change RLS, tool permission, or action approval.
    "bravo_user_guide": (("user_guide", "mindmap", "basic_rule"), "end_user_guidance",
                          ("end_user_guidance",)),
    "implementation": (("technical_manual", "kqpt_ptnv", "report_template", "basic_rule"),
                       "implementation", ("implementation_support", "technical_impact")),
    # The UI must not expose this until approved ISMS/policy sources exist. Keeping the route
    # fail-closed protects the API surface from silently searching unrelated BRAVO material.
    "isms": (("legal_standard",), "governance", ("governance_audit",)),
}


def route_for_profile(query: str, profile: str = "auto") -> KnowledgeRoute:
    """Apply an explicit product profile before retrieval, otherwise use deterministic routing."""
    if profile == "auto":
        return route_query(query)
    source_types, lifecycle_stage, playbook_modes = _PROFILE_ROUTES.get(profile, _PROFILE_ROUTES["bravo_user_guide"])
    intent = infer_query_intent(query)
    return KnowledgeRoute(
        source_types=source_types,
        modules=intent.modules,
        lifecycle_stage=lifecycle_stage,
        playbook_modes=playbook_modes,
        reason=f"profile:{profile}",
    )
