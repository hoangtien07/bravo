"""Evidence gate for deciding whether full GraphRAG is justified.

This does not implement GraphRAG.  It prevents an expensive graph stack from becoming a remedy
for metadata-routing regressions by requiring a blinded relation-heavy benchmark first.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from app.utils.yaml_compat import safe_load_file


@dataclass(frozen=True)
class GraphRAGMetrics:
    overall_quality: float
    relation_quality: float
    relation_cases: int
    p95_latency_ms: float


@dataclass(frozen=True)
class GraphRAGGateResult:
    promote: bool
    reasons: tuple[str, ...]
    relation_lift: float
    overall_regression: float
    latency_multiplier: float


def _metrics(raw: dict) -> GraphRAGMetrics:
    try:
        out = GraphRAGMetrics(
            overall_quality=float(raw["overall_quality"]),
            relation_quality=float(raw["relation_quality"]),
            relation_cases=int(raw["relation_cases"]),
            p95_latency_ms=float(raw["p95_latency_ms"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("metrics phải có overall_quality, relation_quality, relation_cases, p95_latency_ms") from exc
    if not (0 <= out.overall_quality <= 1 and 0 <= out.relation_quality <= 1
            and out.relation_cases >= 0 and out.p95_latency_ms > 0):
        raise ValueError("metrics ngoài phạm vi hợp lệ")
    return out


def evaluate_gate(baseline: GraphRAGMetrics, candidate: GraphRAGMetrics, thresholds: dict) -> GraphRAGGateResult:
    relation_lift = candidate.relation_quality - baseline.relation_quality
    overall_regression = baseline.overall_quality - candidate.overall_quality
    latency_multiplier = candidate.p95_latency_ms / baseline.p95_latency_ms
    reasons: list[str] = []
    if candidate.relation_cases < int(thresholds["min_relation_cases"]):
        reasons.append("relation sample chưa đủ lớn")
    if relation_lift < float(thresholds["min_relation_lift"]):
        reasons.append("không có cải thiện relation-heavy đủ lớn")
    if overall_regression > float(thresholds["max_overall_regression"]):
        reasons.append("chất lượng tổng thể bị giảm vượt ngưỡng")
    if latency_multiplier > float(thresholds["max_p95_latency_multiplier"]):
        reasons.append("p95 latency vượt ngân sách")
    return GraphRAGGateResult(not reasons, tuple(reasons), relation_lift, overall_regression, latency_multiplier)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python -m app.eval.graphrag_gate BASELINE.json CANDIDATE.json", file=sys.stderr)
        return 2
    thresholds = safe_load_file(Path("file_system/graphrag_gate_thresholds.yaml")) or {}
    baseline = _metrics(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    candidate = _metrics(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))
    result = evaluate_gate(baseline, candidate, thresholds)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0 if result.promote else 1


if __name__ == "__main__":
    raise SystemExit(main())
