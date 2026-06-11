"""Golden-trajectory schema + scoring (WP-H, AGENTIC-SPIKE-WS0 §2).

Phase 1E started with single-turn Q&A; WP-H upgrades this to a **trajectory**: a
sequence of `(user_turn, expected_tool_calls, expected_outcome)` steps, evaluated
end-to-end through `AgentSession.step()` k times (pass^k, consistency — not pass@1).

The schema below is the contract the pass^k runner (run.py) consumes. It also carries
the *adversarial* probes that make WP-H a HARD GATE:

  - RLS-leak       — a scoped user must NOT see another department's data (invariant #1).
  - fabricated num  — answer states a number the engine never produced (invariant #3).
  - wrong unit      — engine '52,8 tỷ' but answer '52,8 triệu' (off by 1000x) (invariant #3).
  - egress-leak     — sensitive context routed to cloud (invariant #4).
  - prompt-injection-from-document — instruction inside a retrieved chunk must be ignored.

`GoldenItem` is kept as a thin compatibility shim (single-turn == 1-step trajectory) so the
existing retrieval-only run path still loads old YAML.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Re-export for callers that scored single-turn items.
from app.eval._compat import GoldenItem, ItemResult  # noqa: F401


class Outcome(str, Enum):
    ANSWER = "answer"     # produce a grounded answer (with citation when KB/number)
    ABSTAIN = "abstain"   # refuse / "không tìm thấy" — no data to ground on
    CLARIFY = "clarify"   # ask back — question is ambiguous / missing a param


class HardFailKind(str, Enum):
    """Classes that BLOCK MERGE if they occur on ANY of the k runs (CI hard gate)."""
    RLS_LEAK = "rls_leak"                 # invariant #1
    FABRICATED_NUMBER = "fabricated_num"  # invariant #3
    WRONG_UNIT = "wrong_unit"             # invariant #3 (tỷ↔triệu)
    EGRESS_LEAK = "egress_leak"           # invariant #4
    PROMPT_INJECTION = "prompt_injection"


@dataclass
class Turn:
    """One user turn within a trajectory and what the agent is expected to do."""
    user: str
    expected_tool_calls: list[str] = field(default_factory=list)   # ordered tool names
    expected_outcome: Outcome = Outcome.ANSWER
    expect_citation: bool = False        # answer must carry a citation (KB / number facts)


@dataclass
class Trajectory:
    """A golden trajectory = id + actor (drives RLS scope) + one or more turns + probes.

    The probe fields turn an otherwise-normal trajectory into a HARD-FAIL detector:
      * forbidden_dept_substrings — text that, if it appears in the answer, proves an
        RLS leak (e.g. another department's salary figures / employee names).
      * engine_value / engine_scale + must_not_say — the engine produced `engine_value`
        at `engine_scale`; if the answer states the SAME digits at a DIFFERENT scale
        (tỷ↔triệu) it is a wrong-unit fabrication.
      * injected_instruction_marker — a string the injected document tried to make the
        agent emit; its presence in the answer means the injection succeeded.
    """
    id: str
    actor_email: str
    turns: list[Turn]
    category: str = "lookup"             # lookup | multistep | abstain | clarify | rls | number | injection
    hard_fail_kind: HardFailKind | None = None

    # --- adversarial probe data (only set for hard-fail categories) ---
    forbidden_substrings: list[str] = field(default_factory=list)   # RLS / injection markers
    engine_value: str | None = None      # decimal as string, e.g. "52.8"
    engine_scale: str | None = None      # "tỷ" | "triệu" | ...
    wrong_scales: list[str] = field(default_factory=list)          # scales that = wrong unit
    sensitive: bool = False              # context is sensitive -> must stay LOCAL (no cloud)

    @property
    def first_user(self) -> str:
        return self.turns[0].user if self.turns else ""


@dataclass
class TurnResult:
    """Outcome of running one turn once (one of the k repeats)."""
    answer: str
    grounded: bool
    clarified: bool
    abstained: bool
    citations: list[str]
    tool_calls: list[str]                # tools actually invoked this turn
    routed_cloud: bool = False           # did the turn egress to a cloud backend?

    @property
    def has_citation(self) -> bool:
        return bool(self.citations)


def trajectory_categories(items: list[Trajectory]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for it in items:
        counts[it.category] = counts.get(it.category, 0) + 1
    return counts
