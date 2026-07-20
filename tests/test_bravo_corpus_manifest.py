from __future__ import annotations

from pathlib import Path

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


def test_b8r4_sources_do_not_inherit_b10r1_approval():
    manifest = load_manifest(_MANIFEST)
    idx = manifest_index(manifest, _FS)

    b8_rows = [meta for path, meta in idx.items() if "B8R4" in path.upper()]
    assert b8_rows
    assert all(meta["doc_version"] == "B8R4" for meta in b8_rows)
    assert all(meta["approved_status"] != "approved" for meta in b8_rows)
