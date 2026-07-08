"""Manifest per-deploy (deploy/site.yaml) — config-as-data đọc lúc BOOT (ADR-0018 packaging).

Khai báo cho MỘT deployment (single-tenant): vertical bật, phòng ban (tên hiển thị), feature
flags, model routing. Đọc MỘT LẦN lúc boot trong Settings.validate_boot() và fail-closed nếu
manifest sai — "xuất-file-để-nhập / bật-tắt-vertical là quyết định vận hành, không phải nợ".

KHÔNG resolve per-request / per-tenant: đó là multi-tenant SaaS — GATE tới L3 (ADR-0016 CUT#7).
"Đóng gói theo doanh nghiệp" = deployment/DB RIÊNG mỗi công ty, mỗi cái một site.yaml.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# AP = mũi nhọn ship (ADR-0016). Anomaly/Tax/Graph đóng băng 🧊 — chỉ bật cho DEMO NỘI BỘ, không
# phải cam kết sản xuất. Manifest chỉ được liệt kê trong tập này (fail-closed với tên lạ).
KNOWN_VERTICALS = frozenset({"ap", "anomaly", "tax", "graph"})


class SiteConfigError(RuntimeError):
    """Manifest deploy sai/không hợp lệ — fail-closed lúc boot."""


@dataclass(frozen=True)
class SiteConfig:
    site: str
    enabled_verticals: tuple[str, ...]
    departments: tuple[str, ...] = ()
    raw: dict = field(default_factory=dict)


def load_site_config(path: str) -> SiteConfig:
    """Nạp + validate manifest. Raise SiteConfigError nếu thiếu/sai (fail-closed)."""
    p = Path(path)
    if not p.exists():
        raise SiteConfigError(f"[site] không tìm thấy manifest: {path}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise SiteConfigError("[site] site.yaml không phải mapping YAML")
    site = raw.get("site")
    if not site:
        raise SiteConfigError("[site] thiếu trường 'site' (tên deployment)")
    verticals = raw.get("enabled_verticals")
    if not isinstance(verticals, list) or not verticals:
        raise SiteConfigError("[site] 'enabled_verticals' rỗng/không phải list")
    unknown = [v for v in verticals if v not in KNOWN_VERTICALS]
    if unknown:
        raise SiteConfigError(
            f"[site] vertical không hợp lệ: {unknown} (hợp lệ: {sorted(KNOWN_VERTICALS)})")
    depts = raw.get("departments") or []
    if not isinstance(depts, list):
        raise SiteConfigError("[site] 'departments' phải là list")
    return SiteConfig(site=str(site), enabled_verticals=tuple(verticals),
                      departments=tuple(str(d) for d in depts), raw=raw)


def payload_checksum(path: str | Path) -> str:
    """SHA-256 của một file payload (rule/COA/knowledge) — verify integrity khi giao air-gap.

    Air-gap RUNBOOK: sinh checksum ở nguồn, ký/gửi kèm; nơi nhận đối chiếu trước khi bind-mount.
    KHÔNG dùng flag-service từ xa (lỗi chí mạng cho khách air-gap) — mọi cấu hình đọc file LOCAL."""
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
