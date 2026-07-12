"""Deterministic BRAVO query intent hints for retrieval routing.

This is not an LLM classifier. It is a small, auditable set of BRAVO-specific hints that
turns query wording into preferred corpus metadata (`source_type`, `module`). The goal is
to reduce obvious source mix-ups: schema questions should not be answered from end-user
guides, and operation questions should not be answered from DLL manuals.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class BravoQueryIntent:
    source_types: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    lifecycle_stage: str | None = None

    @property
    def has_hints(self) -> bool:
        return bool(self.source_types or self.modules or self.lifecycle_stage)


def _norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(
        ch for ch in decomposed
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"\s+", " ", stripped.replace("đ", "d")).strip()


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(n in text for n in needles)


_MODULE_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("purchase", ("mua hang", "nha cung cap", "ncc", "phieu nhap mua", "nhap khau",
                  "don dat hang mua", "po", "rfq", "bao gia ncc", "cong no phai tra")),
    ("sale", ("ban hang", "don hang ban", "bao gia khach", "hoa don ban", "doanh thu")),
    ("sales_retail", ("ban le", "pos", "cua hang", "voucher", "diem thuong")),
    ("inventory", ("ton kho", "kho", "kiem ke", "nhap xuat ton", "lo serial", "barcode")),
    ("accounting", ("ke toan", "hach toan", "but toan", "tai khoan", "cong no", "bctc", "thue")),
    ("hrm", ("hrm", "nhan su", "luong", "cham cong", "bhxh", "tuyen dung")),
    ("production", ("san xuat", "bom", "lenh san xuat", "gia thanh", "oee")),
    ("qc", ("qc", "iqc", "pqc", "oqc", "kiem tra chat luong", "khong dat chat luong")),
    ("crm", ("crm", "lead", "prospect", "opportunity", "chien dich", "khieu nai")),
    ("task", ("cong viec", "task", "du an", "wbs", "kanban", "gantt")),
    ("mobile", ("mobile", "offline", "dien thoai", "thiet bi di dong")),
    ("dashboard", ("dashboard", "bang dieu khien", "kpi", "chi tieu quan tri")),
    ("report", ("bao cao", "mau in", "report", "cong thuc bao cao")),
    ("system", ("phan quyen", "audit", "log", "khoa du lieu", "2fa", "captcha", "mat khau")),
)


def infer_query_intent(query: str) -> BravoQueryIntent:
    q = _norm(query)
    source_types: list[str] = []
    modules: list[str] = []
    lifecycle_stage: str | None = None

    if _has_any(q, (
        "b30", "b20", "b10", "b00", "b30bizdoc", "b30accdoc", "bang ", "table",
        "view", "procedure", "stored", "usp_", "ufn_", "function", "rowid", "stt",
        "layout", "editor", "explorer", "datasource", "dll", "getdata",
        "evaluator", "commandvalidator", "commandvalidators", "b00command",
        "reporter", "uspcaller", "wizard", "taskman", "attachfile", "expression",
        "bravouploadfilebox", "bravopictureinputbox",
        # dev/customization/integration — trước đây thiếu nên câu kỹ thuật kéo nhầm user_guide
        "tuy bien", "tuy chinh", "customize", "customise", "khai bao",
        "tich hop", "webservice", "web service", " api", "api ", "restful",
        "loai giao dich", "loai chung tu", "dinh khoan tu dong", "cau hinh he thong",
    )):
        source_types.extend(["technical_manual", "kqpt_ptnv"])
        modules.append("platform")
        lifecycle_stage = "technical_design"

    if _has_any(q, (
        "kqpt", "ptnv", "pham vi", "muc tieu", "yeu cau", "acceptance",
        "testcase", "test case", "kiem thu", "cau hoi khao sat", "actor",
    )):
        source_types.extend(["kqpt_ptnv", "mindmap", "user_guide"])
        lifecycle_stage = "ba_analysis"

    if _has_any(q, (
        "thao tac", "cach ", "huong dan", "menu", "man hinh", "phieu ", "lam the nao",
        "dung the nao", "quy trinh", "luong ", "buoc ",
    )):
        source_types.extend(["user_guide", "mindmap"])
        lifecycle_stage = lifecycle_stage or "end_user_guidance"

    # Overview/definition/scope queries ("... là gì", "quản lý ... gồm những chức năng gì",
    # "tổng quan ...") mô tả CHỨC NĂNG phân hệ -> ưu tiên user guide/mindmap thay vì tài liệu
    # phân tích-thiết kế (kqpt_ptnv) hay DLL. Không đặt lifecycle kỹ thuật -> tránh kéo về schema.
    if _has_any(q, (
        "quan ly", "chuc nang", "tong quan", "gom nhung gi", "bao gom", "gioi thieu",
        " la gi", "nhung gi", "chuc nang gi",
    )):
        source_types.extend(["user_guide", "mindmap"])
        lifecycle_stage = lifecycle_stage or "end_user_guidance"

    if _has_any(q, (
        "trien khai", "go live", "go-live", "cai dat", "don vi co so", "branch",
        "so du dau ky", "du lieu dau ky", "license", "tham so",
    )):
        source_types.extend(["technical_manual", "basic_rule", "kqpt_ptnv"])
        modules.extend(["system", "platform"])
        lifecycle_stage = "implementation"

    if _has_any(q, ("dashboard", "bao cao", "mau in", "chi tieu", "cong thuc")):
        source_types.extend(["report_template", "kqpt_ptnv", "technical_manual", "user_guide"])
        lifecycle_stage = lifecycle_stage or "management_reporting"

    for module, needles in _MODULE_HINTS:
        if _has_any(q, needles):
            modules.append(module)

    return BravoQueryIntent(
        source_types=tuple(dict.fromkeys(source_types)),
        modules=tuple(dict.fromkeys(modules)),
        lifecycle_stage=lifecycle_stage,
    )


def _extra_value(obj: object, key: str) -> str:
    extra = getattr(obj, "extra", None) or {}
    return str(extra.get(key) or "").strip().lower()


def boost_for_bravo_intent(query: str, results: list) -> list:
    """Boost in-place and return results sorted by BRAVO metadata hints.

    Scores from RRF are small; the boost is intentionally modest but enough to lift an
    otherwise similar candidate with the right source taxonomy.
    """
    intent = infer_query_intent(query)
    if not intent.has_hints or not results:
        return results

    source_types = set(intent.source_types)
    modules = set(intent.modules)
    # Q8 (anti-KQPT dominance): for pure how-to / end-user questions, DEMOTE BA-analysis docs
    # (kqpt_ptnv = 41% of the corpus, wins retrieval by volume and makes answers read like
    # system analysis). Only when the how-to intent did NOT itself request kqpt_ptnv.
    demote_kqpt = (
        intent.lifecycle_stage == "end_user_guidance" and "kqpt_ptnv" not in source_types
    )
    for r in results:
        boost = 0.0
        stype = _extra_value(r, "source_type")
        if stype in source_types:
            boost += 0.05
        if _extra_value(r, "module") in modules:
            boost += 0.025
        if intent.lifecycle_stage and _extra_value(r, "lifecycle_stage") == intent.lifecycle_stage:
            boost += 0.015
        if demote_kqpt and stype == "kqpt_ptnv":
            boost -= 0.04
        r.score = float(getattr(r, "score", 0.0)) + boost

    return sorted(results, key=lambda r: r.score, reverse=True)
