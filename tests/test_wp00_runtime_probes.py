from scripts.wp00_runtime_probes import MARKERS, NAMESPACE, _id, _report


def test_probe_ids_are_deterministic_and_isolated_by_run_id():
    assert _id("run-a", "chunk-a") == _id("run-a", "chunk-a")
    assert _id("run-a", "chunk-a") != _id("run-b", "chunk-a")
    assert _id("run-a", "chunk-a").version == 5
    assert NAMESPACE.version == 4


def test_probe_report_is_redaction_safe_and_requires_every_check():
    report = _report(run_id="synthetic-run", mode="worker",
                     checks={"scope": True, "no_leak": False}, details={"count": 2})
    assert report["synthetic_only"] is True
    assert report["passed"] is False
    assert set(MARKERS) == {"a", "b", "global"}
