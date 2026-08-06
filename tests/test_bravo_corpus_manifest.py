from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion.manifest import load_manifest, manifest_index


_ROOT = Path(__file__).resolve().parents[1]
_FS = _ROOT / "file_system"
_MANIFEST = _FS / "bravo_corpus_manifest.yaml"


def test_bravo_manifest_maps_purchase_userguide():
    manifest = load_manifest(_MANIFEST)
    idx = manifest_index(manifest, _FS)
    meta = idx["UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter08_Purchases.pdf"]

    assert meta["source_type"] == "user_guide"
    assert meta["module"] == "purchase"
    assert meta["business_area"] == "procure_to_pay"
    assert meta["knowledge_type"] == "Chuong 08 - Purchases"


def test_bravo_manifest_maps_mindmap_and_technical_manual():
    manifest = load_manifest(_MANIFEST)
    idx = manifest_index(manifest, _FS)

    assert idx["Mindmaps/Mindmap_Purchase.md"]["source_type"] == "mindmap"
    assert idx["TaiLieuBravo10_KhoiKyThuat.docx"]["source_type"] == "technical_manual"
    assert idx["TaiLieuBravo10_KhoiKyThuat.docx"]["lifecycle_stage"] == "technical_design"


def test_manifest_does_not_upgrade_b8r4_kqpt_sources_to_b10r1_approved():
    manifest = load_manifest(_MANIFEST)
    idx = manifest_index(manifest, _FS)

    for path in (
        "KQPT_PTNV/02_NB_MB2023_011_KQPT_QLCV_B8R4_v1_1.pdf",
        "KQPT_PTNV/14_NB_MB2024_014_KQPT_B8R4_FileAttached.pdf",
    ):
        meta = idx[path]
        assert meta["doc_version"] == "B8R4"
        assert meta["approved_status"] == "draft"
        assert meta["owner"] == "source_owner_unverified"
        assert meta["customer_scope"] == "unknown"


def test_manifest_rejects_filename_version_that_conflicts_with_metadata(tmp_path):
    manifest = {
        "defaults": {
            "doc_version": "B10R1", "owner": "bravo_product", "approved_status": "approved",
            "effective_date": None, "customer_scope": "global",
        },
        "sources": [{"path": "KQPT_PTNV/example_B8R4.pdf", "source_type": "kqpt_ptnv"}],
    }

    with pytest.raises(ValueError, match="filename declares 'B8R4'"):
        manifest_index(manifest, tmp_path)


def test_manifest_rejects_source_missing_authority_metadata(tmp_path):
    manifest = {"system_version": "B10R1", "sources": [{"path": "unversioned.pdf", "source_type": "user_guide"}]}

    with pytest.raises(ValueError, match="missing authority metadata"):
        manifest_index(manifest, tmp_path)
