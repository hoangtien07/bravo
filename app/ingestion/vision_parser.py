"""Q9 — vision OCR for scanned PDFs (ADR-0019 lifts the ADR-0009 OCR descope under cloud-only).

Renders each page to an image (pypdfium2, optional dep) and asks a vision-capable cloud model
to transcribe it to Markdown, preserving tables. Output blocks carry page provenance and
`evidence_level="derived_summary"` + `is_scanned=True` so downstream code knows the numbers
are TRANSCRIBED, not engine truth — they stay quote-level with a page citation and NEVER feed
the number verify-gate (invariant #3).

Sync (mirrors embedding.py) so the sync `parse()` dispatcher can call it. Enabled only when
settings.vision_ocr_enabled AND pypdfium2 is installed AND a vision model is configured;
otherwise raises a clear error the ingestion pipeline surfaces as a failed source.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.ingestion.parser import ParsedBlock

_settings = get_settings()

_PROMPT = (
    "Bạn là công cụ OCR. Chép lại TOÀN BỘ nội dung trang tài liệu trong ảnh sang Markdown "
    "tiếng Việt, GIỮ NGUYÊN bảng biểu (dùng bảng Markdown), số và mã chứng từ ĐÚNG như hiển "
    "thị. KHÔNG suy diễn, KHÔNG thêm thông tin ngoài ảnh. Nếu trang trống, trả về chuỗi rỗng."
)


@lru_cache
def _vision_client():
    from openai import OpenAI  # lazy
    return OpenAI(base_url=_settings.cloud_base_url or None,
                  api_key=_settings.cloud_api_key, timeout=60.0, max_retries=2)


def _vision_model() -> str:
    return _settings.vision_model or _settings.cloud_model


def _render_pages(path: str | Path, max_pages: int) -> list[bytes]:
    """Render PDF pages to PNG bytes via pypdfium2 (optional dep)."""
    try:
        import pypdfium2 as pdfium  # lazy optional
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "[vision] Cần pypdfium2 để OCR PDF scan — cài extra: uv pip install pypdfium2"
        ) from exc
    pdf = pdfium.PdfDocument(str(path))
    out: list[bytes] = []
    for i in range(min(len(pdf), max_pages)):
        bitmap = pdf[i].render(scale=2.0)          # ~144 DPI
        pil = bitmap.to_pil()
        import io
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        out.append(buf.getvalue())
    return out


def _transcribe(png: bytes) -> str:
    b64 = base64.b64encode(png).decode()
    resp = _vision_client().chat.completions.create(
        model=_vision_model(),
        messages=[{"role": "user", "content": [
            {"type": "text", "text": _PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]}],
        temperature=0.0,
    )
    return (resp.choices[0].message.content or "").strip()


def parse_pdf_vision(path: str | Path) -> list[ParsedBlock]:
    """Transcribe a scanned PDF into per-page ParsedBlocks (numbers stay quote-level)."""
    if not _settings.vision_ocr_enabled:
        raise RuntimeError("[vision] vision_ocr_enabled=false — không OCR PDF scan.")
    if not _vision_model():
        raise RuntimeError("[vision] chưa cấu hình vision_model/cloud_model.")
    blocks: list[ParsedBlock] = []
    for i, png in enumerate(_render_pages(path, _settings.vision_max_pages), start=1):
        text = _transcribe(png)
        if not text:
            continue
        blocks.append(ParsedBlock(
            text=text, page_number=i,
            extra={"format": "pdf_scan", "is_scanned": True,
                   "evidence_level": "derived_summary"},
        ))
    return blocks
