"""Query expansion viết tắt nghiệp vụ VN (council 2026-07-12 #6) — tất định."""
from __future__ import annotations

from app.rag.vn_terms import expand_abbreviations


def test_expands_common_accounting_abbreviations():
    assert "công cụ dụng cụ" in expand_abbreviations("khai báo CCDC")
    assert "cân đối phát sinh" in expand_abbreviations("cach len bao cao CDPS")
    assert "tài sản cố định" in expand_abbreviations("khấu hao TSCĐ")


def test_keeps_original_token_and_no_double_expansion():
    out = expand_abbreviations("khai báo CCDC")
    assert "CCDC" in out                                   # từ gốc còn nguyên (lexical khớp mã)
    assert out.count("công cụ dụng cụ") == 1
    # cụm đầy đủ đã có sẵn -> không chèn lặp
    out2 = expand_abbreviations("khai báo CCDC công cụ dụng cụ")
    assert out2.count("công cụ dụng cụ") == 1


def test_ambiguous_and_plain_text_untouched():
    assert expand_abbreviations("số dư TK 331") == "số dư TK 331"   # TK nhập nhằng -> bỏ qua
    assert expand_abbreviations("cách tạo phiếu nhập mua") == "cách tạo phiếu nhập mua"
