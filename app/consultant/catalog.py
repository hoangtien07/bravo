"""Load the SME-owned workflow catalog without making YAML an execution surface."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.consultant.contracts import GoalCard, WorkflowCard
from app.utils.yaml_compat import safe_load_file

DEFAULT_CATALOG = Path("file_system/bravo_consultant_cards.yaml")


@lru_cache(maxsize=4)
def load_catalog(path: str = str(DEFAULT_CATALOG)) -> tuple[dict[str, GoalCard], dict[str, WorkflowCard]]:
    raw = safe_load_file(Path(path)) or {}
    goals = {item["goal_type"]: GoalCard(**item) for item in raw.get("goals", [])}
    workflows = {item["id"]: WorkflowCard(**item) for item in raw.get("workflows", [])}
    if not goals or not workflows:
        raise ValueError("consultant catalog requires goals and workflows")
    for workflow in workflows.values():
        if workflow.goal_type not in goals:
            raise ValueError(f"workflow {workflow.id} references unknown goal {workflow.goal_type}")
        node_ids = {node.id for node in workflow.nodes}
        for node in workflow.nodes:
            missing = set(node.prerequisite_ids) - node_ids
            if missing:
                raise ValueError(f"workflow {workflow.id}/{node.id} missing prerequisites {sorted(missing)}")
        if workflow.evidence_status == "verified" and not workflow.evidence_refs:
            raise ValueError(f"workflow {workflow.id} is verified but has no evidence_refs")
        if workflow.evidence_status == "sme_reviewed" and not workflow.reviewed_by:
            raise ValueError(f"workflow {workflow.id} is sme_reviewed but has no reviewed_by")
    return goals, workflows


def match_workflow(question: str, path: str = str(DEFAULT_CATALOG)) -> WorkflowCard | None:
    _goals, workflows = load_catalog(path)
    folded = question.casefold()
    ranked = [
        (sum(1 for trigger in wf.triggers if trigger.casefold() in folded), wf)
        for wf in workflows.values()
    ]
    ranked = [item for item in ranked if item[0]]
    return max(ranked, key=lambda item: item[0])[1] if ranked else None
