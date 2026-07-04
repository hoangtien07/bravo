"""Engine soi bất thường (TẤT ĐỊNH) — chỉ FLAG, KHÔNG tự sửa/kết luận gian lận (ANOMALY-AGENT.md).

Số liệu lấy TỪ DỮ LIỆU (Decimal), KHÔNG do LLM sinh (invariant #3). Ba luật demo:
  - TRÙNG: cùng (NCC, số tiền, ngày) -> nghi hoá đơn/bút toán trùng.
  - SỐ TRÒN LỚN: số tiền chia hết 10tr và >= 100tr.
  - NGOÀI GIỜ: hạch toán lúc >=20h hoặc <6h.
Một bút toán kích nhiều luật -> mức độ cao hơn. Bất thường cài sẵn (fixture) được đưa vào nguyên.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

from app.data_layer import money

ROUND_UNIT = Decimal("10000000")    # 10 triệu
ROUND_MIN = Decimal("100000000")    # số tròn "lớn" >= 100tr
OFF_START, OFF_END = 20, 6          # ngoài giờ: giờ >= 20 hoặc < 6


@dataclass
class Flag:
    loai: str
    chung_tu: str
    so_tien: str                    # str cho JSON/verify-gate
    mo_ta: str
    muc_do: int                     # severity = số luật kích hoạt
    bang_chung: list[str] = field(default_factory=list)

    def to_payload(self) -> dict:
        return {"loai": self.loai, "chung_tu": self.chung_tu, "so_tien": self.so_tien,
                "mo_ta": self.mo_ta, "muc_do": self.muc_do, "bang_chung": self.bang_chung,
                "is_demo": True}


def _hour(gio: object) -> int:
    try:
        return int(str(gio).split(":")[0])
    except Exception:
        return 12


def detect(journal_entries: list | None, seeded: list | None = None) -> list[Flag]:
    entries = journal_entries or []
    flags: list[Flag] = []

    def key(e: dict) -> tuple:
        return (e.get("ncc"), str(e.get("so_tien")), e.get("ngay"))

    counts = Counter(key(e) for e in entries)
    for e in entries:
        reasons: list[str] = []
        st = money.D(e.get("so_tien", 0))
        if counts[key(e)] > 1:
            reasons.append("Trùng NCC + số tiền + ngày (nghi hoá đơn/bút toán trùng)")
        if st >= ROUND_MIN and st % ROUND_UNIT == 0:
            reasons.append(f"Số tròn lớn ({st:,.0f}đ)")
        h = _hour(e.get("gio"))
        if h >= OFF_START or h < OFF_END:
            reasons.append(f"Hạch toán ngoài giờ ({e.get('gio')})")
        if reasons:
            flags.append(Flag(
                loai="but_toan_bat_thuong", chung_tu=str(e.get("id")), so_tien=str(st),
                mo_ta=f"{e.get('dien_giai', '')} — {e.get('ncc', '')}".strip(" —"),
                muc_do=len(reasons), bang_chung=reasons,
            ))

    for a in (seeded or []):
        vnd = money.D(a.get("value", 0)) * money.scale_factor(a.get("scale"))
        flags.append(Flag(
            loai=a.get("loai", "bat_thuong"), chung_tu=str(a.get("chung_tu")),
            so_tien=str(money.quantize(vnd)), mo_ta=a.get("mo_ta", ""),
            muc_do=2, bang_chung=[a.get("mo_ta", "")],
        ))

    flags.sort(key=lambda f: f.muc_do, reverse=True)
    return flags
