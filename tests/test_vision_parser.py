"""Q9 — vision OCR parser: block shaping + evidence-level guard (render + LLM mocked)."""
from __future__ import annotations

import pytest

from app.ingestion import vision_parser


def test_disabled_by_default_raises():
    # vision_ocr_enabled defaults False -> must not silently OCR.
    with pytest.raises(RuntimeError, match="vision_ocr_enabled"):
        vision_parser.parse_pdf_vision("whatever.pdf")


def test_scanned_pdf_blocks_are_quote_level(monkeypatch):
    monkeypatch.setattr(vision_parser._settings, "vision_ocr_enabled", True)
    monkeypatch.setattr(vision_parser._settings, "cloud_model", "gpt-4o")
    # Render -> 2 fake page images; transcription -> deterministic text.
    monkeypatch.setattr(vision_parser, "_render_pages", lambda p, n: [b"png1", b"png2"])
    monkeypatch.setattr(vision_parser, "_transcribe",
                        lambda png: "Hoá đơn số 007, tiền 5.000.000 đ")

    blocks = vision_parser.parse_pdf_vision("scan.pdf")
    assert len(blocks) == 2
    for i, b in enumerate(blocks, start=1):
        assert b.page_number == i
        # Numbers from a scan are quote-level, never engine truth (invariant #3).
        assert b.extra["is_scanned"] is True
        assert b.extra["evidence_level"] == "derived_summary"
        assert "5.000.000" in b.text  # transcribed verbatim, cited by page


def test_empty_page_transcription_is_skipped(monkeypatch):
    monkeypatch.setattr(vision_parser._settings, "vision_ocr_enabled", True)
    monkeypatch.setattr(vision_parser._settings, "cloud_model", "gpt-4o")
    monkeypatch.setattr(vision_parser, "_render_pages", lambda p, n: [b"png1", b"png2"])
    monkeypatch.setattr(vision_parser, "_transcribe",
                        lambda png: "" if png == b"png1" else "trang 2 có chữ")
    blocks = vision_parser.parse_pdf_vision("scan.pdf")
    assert len(blocks) == 1
    assert blocks[0].page_number == 2
