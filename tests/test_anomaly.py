"""Engine soi bất thường (tất định) — trên mock journal_entries + anomalies cài sẵn."""
from __future__ import annotations

from app.agent.anomaly import detect
from app.data_layer.mock_source import MockDataSource


def test_detect_flags_expected_cases():
    src = MockDataSource()
    flags = detect(src.fetch_block("journal_entries"), src.fetch_block("anomalies"))
    ct = {f.chung_tu for f in flags}

    # cặp trùng (cùng NCC+số tiền+ngày)
    assert "PKT-2026-0210" in ct and "PKT-2026-0211" in ct
    # số tròn lớn + ngoài giờ
    assert "PKT-2026-0225" in ct and "PKT-2026-0226" in ct
    # bất thường cài sẵn được đưa vào
    assert "HD-2026-0421/0422" in ct
    # bút toán bình thường KHÔNG bị cờ
    assert "PKT-2026-0230" not in ct


def test_severity_and_numbers_from_data():
    src = MockDataSource()
    flags = detect(src.fetch_block("journal_entries"), src.fetch_block("anomalies"))
    f = next(x for x in flags if x.chung_tu == "PKT-2026-0225")
    assert f.muc_do >= 2                       # số tròn + ngoài giờ
    assert f.so_tien == "500000000"            # số lấy TỪ DỮ LIỆU (không LLM)
    assert any("tròn" in r.lower() for r in f.bang_chung)


def test_flags_sorted_by_severity():
    src = MockDataSource()
    flags = detect(src.fetch_block("journal_entries"), src.fetch_block("anomalies"))
    muc = [f.muc_do for f in flags]
    assert muc == sorted(muc, reverse=True)
