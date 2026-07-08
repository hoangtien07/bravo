"""Config-as-data lúc boot (Phase 2): manifest deploy + overlay knowledge dir (ADR-0018)."""
from __future__ import annotations

import pytest

from app.accounting import rules_governance as gov
from app.config import Settings
from app.site_config import SiteConfigError, load_site_config, payload_checksum

_VALID = """
site: acme
enabled_verticals: [ap, tax]
departments: [Kế toán, Kinh doanh]
"""


def _write(tmp_path, text, name="site.yaml"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


# --- load_site_config: fail-closed validation ---
def test_valid_manifest(tmp_path):
    sc = load_site_config(_write(tmp_path, _VALID))
    assert sc.site == "acme"
    assert sc.enabled_verticals == ("ap", "tax")
    assert "Kế toán" in sc.departments


def test_missing_file():
    with pytest.raises(SiteConfigError):
        load_site_config("/no/such/site.yaml")


def test_missing_site(tmp_path):
    with pytest.raises(SiteConfigError):
        load_site_config(_write(tmp_path, "enabled_verticals: [ap]\n"))


def test_empty_verticals(tmp_path):
    with pytest.raises(SiteConfigError):
        load_site_config(_write(tmp_path, "site: a\nenabled_verticals: []\n"))


def test_unknown_vertical(tmp_path):
    with pytest.raises(SiteConfigError, match="không hợp lệ"):
        load_site_config(_write(tmp_path, "site: a\nenabled_verticals: [ap, crypto_mining]\n"))


def test_checksum_stable(tmp_path):
    p = _write(tmp_path, _VALID)
    assert payload_checksum(p) == payload_checksum(p)
    assert len(payload_checksum(p)) == 64


# --- validate_boot fail-closed khi manifest sai (mọi env) ---
def test_validate_boot_rejects_bad_manifest(tmp_path):
    bad = _write(tmp_path, "site: a\nenabled_verticals: []\n", "bad.yaml")
    with pytest.raises(SiteConfigError):
        Settings(env="local", site_config=bad).validate_boot()


def test_validate_boot_ok_with_valid_manifest(tmp_path):
    Settings(env="local", site_config=_write(tmp_path, _VALID)).validate_boot()  # không raise


# --- BRAVO_KNOWLEDGE_DIR overlay: overlay-trước, fallback in-package ---
def test_resolve_overlay_then_package(tmp_path, monkeypatch):
    class _S:
        knowledge_dir = str(tmp_path)
    monkeypatch.setattr(gov, "get_settings", lambda: _S())
    # chưa có file overlay -> fallback bản in-package
    assert gov.resolve_data_file("statutory_rules_vn.yaml") == gov._PKG_DATA / "statutory_rules_vn.yaml"
    # tạo file overlay -> dùng bản overlay (cập nhật rule không rebuild image)
    (tmp_path / "statutory_rules_vn.yaml").write_text("x: 1", encoding="utf-8")
    assert gov.resolve_data_file("statutory_rules_vn.yaml") == tmp_path / "statutory_rules_vn.yaml"


def test_resolve_no_override_uses_package(monkeypatch):
    class _S:
        knowledge_dir = ""
    monkeypatch.setattr(gov, "get_settings", lambda: _S())
    assert gov.resolve_data_file("coa_tt99_v2025.yaml") == gov._PKG_DATA / "coa_tt99_v2025.yaml"
