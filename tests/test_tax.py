"""Engine đối chiếu thuế (tất định) — hoá đơn ↔ tờ khai trên mock."""
from __future__ import annotations

from app.agent.tax import reconcile
from app.data_layer.mock_source import MockDataSource


def test_reconcile_output_mismatch_and_bad_rate():
    src = MockDataSource()
    flags = reconcile(src.fetch_block("invoices"), src.fetch_block("tax_returns"))
    loais = {f.loai for f in flags}
    assert "lech_thue_dau_ra" in loais        # đầu ra thực 11.9tr ≠ khai 9tr
    assert "thue_suat_la" in loais            # HD-0009 thuế suất 15%
    assert "lech_thue_dau_vao" not in loais   # đầu vào khớp 6.5tr


def test_reconcile_diff_from_data():
    src = MockDataSource()
    flags = reconcile(src.fetch_block("invoices"), src.fetch_block("tax_returns"))
    fout = next(f for f in flags if f.loai == "lech_thue_dau_ra")
    assert fout.chenh_lech == "2900000"       # số từ dữ liệu (không LLM)
    assert fout.so_hd_thuc == "11900000" and fout.so_khai == "9000000"
