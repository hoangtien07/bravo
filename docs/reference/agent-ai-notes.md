# agent-ai (Atlas Builder) — Reference Notes

**Là gì:** Hệ **agentic production** (đã có người dùng thật) dựng tờ khai hải quan **ECUS5/VNACCS** cho khách P&G, Panasonic VN (PV), Sumi. Điểm khác biệt: **không có LLM trong pipeline lõi** — tri thức nghiệp vụ sống dạng *file* (Cursor rules + "experiences"), bên dưới là **pipeline Python tất định** với **cổng audit** và **cổng bàn giao (maker-checker)**.

**Vai trò với BRAVO:** đây là **bằng chứng thực chiến** cho 4 nguyên tắc bất biến của BRAVO trong một sản phẩm doanh nghiệp VN đã chạy: *zero-hallucination số liệu*, *con người duyệt trước khi chốt*, *chạy offline hoàn toàn*, *tri thức nghiệp vụ tách khỏi code*. Gần BRAVO về **văn hoá vận hành**, dù khác về domain (hải quan vs kế toán/ERP).

**Stack:** Python 3.10+ thuần · pipeline gọi module con qua `sys.executable` · OCR offline (RapidOCR chính, Tesseract dự phòng) · dữ liệu lookup = CSV/JSON (UTF-8-SIG), nguồn = Excel offline · điều phối bằng Cursor rules (`.mdc`) + experiences (`.md`). **Không gọi LLM trong pipeline xử lý số liệu.**

> ⚠️ Repo này hiện **thiếu dữ liệu cấu hình** để chạy thật (xem §6) — chủ repo lấy được code + rules + experiences nhưng `context/dictionary/` và `context/tariff/` đang rỗng.

---

## 1. "Rules + Experiences" = system prompt + skill library dạng file ⭐ — *điểm vàng*
- `.cursor/rules/TKhai.mdc` (~55KB): **prompt điều phối cấp hệ thống** — định nghĩa 7 skill, logic routing lô, quy tắc gộp invoice, thứ tự ưu tiên tra dictionary, và các **"cấm cứng"** (vd cấm trộn master P&G của skill-02 với master PV của skill-04 trên cùng một lô).
- `.cursor/rules/HSCode.mdc` (~19KB): quy tắc phân loại HS — plausibility, cách verify, **khi nào chỉ cảnh báo** (warn-only, không tự sửa master).
- `.cursor/rules/vietnamese-writing-rules.mdc` (~22KB): quy chuẩn hành văn tiếng Việt.
- `context/experiences/skill-02..08-*.md` (7 file): mỗi file là **domain knowledge của một nghiệp vụ** — phạm vi, bảng mã mặc định, schema canonical, mapping *chứng từ → tag XML*, quy tắc derive, ví dụ, ngoại lệ.

**Lấy cho BRAVO:** đây là hiện thực hoá của ADR-0007 (code chỉ *orchestrate*, tri thức nằm ngoài code). Thay vì nhồi `if loại_chứng_từ == ...` vào Python, BRAVO có thể gom luật kế toán/nghiệp vụ thành **experiences markdown + rule JSON + master CSV** để **kế toán/compliance cập nhật mà không sờ code**. Đây cũng là pattern khớp với `.claude/skills/` của BRAVO nhưng cho *tri thức nghiệp vụ end-user*, không chỉ harness.

## 2. Routing tất định + cưỡng chế dừng khi mâu thuẫn ⭐
- "Bước 0" trong `TKhai.mdc`: `lo_config.json` (skill + customer + MST) **đối chiếu dấu hiệu chứng từ** (BL, AN, invoice, MST người NK) → **chọn đúng một skill**. Mâu thuẫn ⇒ **DỪNG, hỏi người dùng** — *không* mặc định fallback.
- Tách dữ liệu theo skill rất nghiêm: mỗi skill có **một master entry-point riêng** và danh sách **master bị cấm** (vd skill-04 cấm dùng master P&G). Không copy master vào thư mục lô.

**Lấy cho BRAVO:** áp cho phân loại tác vụ (tờ khai/hoá đơn/bút toán). **"Fail loud, không fallback"** + kiểm tra trường bắt buộc trước khi agent bắt đầu = một lá chắn chống hành động sai trên dữ liệu kế toán.

## 3. Cổng audit ↔ cổng bàn giao (maker-checker bằng exit code) ⭐ — *khớp nguyên tắc non-invasive*
- `scripts/build_tokhai_xml_from_canonical.py`: build XML **tất định**; `validate_canonical.py` chạy **trước** build.
- `scripts/audit_runner.py` + `audit_rules.py`: sinh `Audit_<BL>.{json,md,xlsx}` với 3 loại check — **AUTO_XML** (regex/enum/luật cố định), **AUTO_XREF** (đối chiếu XML ↔ chứng từ/dictionary), **MANUAL** (checkpoint cần con người, kèm *bằng chứng* "file X dòng Y"). **Audit chỉ báo cáo, không chặn.**
- `scripts/handover_check.py`: **cổng chặn** — đọc audit, lọc Critical/fail, kiểm `exception_approval.json` → **exit 0 (cho bàn giao)** hoặc **exit ≠ 0 (chặn)**. Approval file chỉ *miễn luật đã được duyệt*, **không** coi là sửa lỗi; **không tạo approval tự động**.

**Lấy cho BRAVO:** đây chính là khuôn **verify-gate + maker-checker** (ADR-0012) ở dạng vận hành thật: *sinh artifact → audit (cảnh báo) → gate (chặn) → người duyệt*. Tách bạch "cảnh báo" và "chặn" là bài học quan trọng; exit-code gate có thể nối thẳng vào CI/dashboard.

## 4. Zero-hallucination: master là nguồn sự thật, agent chỉ verify ⭐
- **HS code lấy từ shipper master, không từ C/O**: C/O chỉ để *đối chiếu* (warn nếu lệch); XML giữ Duty Master.
- `scripts/hs_plausibility.py` (tất định, **cấm gọi LLM**) ghi *bundle gợi ý* → agent Cursor đọc bundle, ghi `hs_plausibility_answer_<BL>.json` (lý do + kết luận). Agent **không suy diễn lại số**, chỉ phán xét trên bằng chứng đã trích.
- **Ngoại lệ mơ hồ → liệt kê ứng viên, không đoán**: POD nhập nhằng → `port_pending_<BL>.json` liệt kê *toàn bộ* ứng viên + set field = null + ghi rationale; con người chọn.
- **Source tracking**: canonical CSV có `source_file`/`source_sheet`/`source_row`; mọi kết luận audit trích dẫn đúng vị trí chứng từ.

**Lấy cho BRAVO:** ánh xạ trực tiếp sang ADR-0004 (LLM không tự tính số) và nguyên tắc 3. **Chứng từ gốc = master, LLM không bao giờ override.** Khi có cảnh báo bất thường (đơn giá lạ, lệch số) → agent ghi memo + *liệt kê ứng viên*, maker xác nhận; tuyệt đối không tự sửa dữ liệu. Mẫu `port_pending` = pattern "needs_confirmation" cho dữ liệu mơ hồ.

## 5. Offline-by-design (dictionary + OCR cục bộ)
- `scripts/builder_paths.py`: dò workspace, chọn template; override qua `ATLAS_BUILDER_WORKSPACE`/`BUILDER_WORKSPACE`.
- Hai tầng dữ liệu: **runtime `context/dictionary/csv/`** (pipeline chỉ đọc CSV) ↔ **nguồn `context/dictionary/source/`** (Excel, chỉ để `export_dictionary_context_to_csv.py --from-source` sinh lại CSV — *không* mở Excel lúc chạy).
- OCR: RapidOCR (`scripts/vie_ocr.py`) là chính; Tesseract dự phòng; `pdf_vision_extract.py` chỉ chạy riêng khi có vision API. **Không gọi vision API trong bước số liệu.**

**Lấy cho BRAVO:** mô hình *nguồn offline → biên dịch sang lookup runtime* là bài học cho cache tri thức/master cục bộ. Khẳng định lại: đường chạy số liệu không cần mạng.

## 6. ⚠️ Cấu hình đang thiếu (chủ repo cần bổ sung để chạy thật)
`context/dictionary/` và `context/tariff/` hiện **rỗng** → code compile được nhưng pipeline **không chạy** vì thiếu lookup. Cần bổ sung:

| Nhóm | File cần có (entry-point in đậm) |
|------|------------------------------|
| skill-02 (P&G FG) | **`ten_hang_library_index.csv`**, `AMAE_Duty_Master_*.csv`, `MA_CANG_*_{HAI_PHONG,CAT_LAI_HCM}.csv`, `pg_customs_office_policy.json` |
| skill-04 (PV nhập) | **`pv_hang_library_index.csv`**, `Master_HS_code_PV_*.csv`, `file_mã_địa_điểm_{xếp,dỡ}_hàng_*.csv` (bắt buộc), `nonwaving_list.csv`, các `pv_*_rules.json` |
| skill-06 (PV xuất) | **`pv_export_factory_index.csv`**, **`pv_export_location_index.csv`**, `pv_hang_library_index.csv` |
| skill-07 (P&G ĐD) | `AMAE_Duty_Master_*.csv` (tra theo **Material number**) |
| skill-08 (Sumi) | **`sumi_hang_library_index.csv`**, `sumi_hang_da_khai_index.csv`, `sumi_un_locode_index.csv` |
| tariff (mọi skill) | `context/tariff/full.csv` (HS 8 số + mô tả + UOM), `context/tariff/chapters/ch01..98.csv` |
| checklist | `context/checklist/checklist_final_vnm.csv` (đã có), template báo cáo audit |

- **Biến môi trường**: `ATLAS_BUILDER_WORKSPACE`/`BUILDER_WORKSPACE`; vision API key (chỉ nếu dùng `pdf_vision_extract.py`).
- **Python deps**: `pymupdf pdfplumber openpyxl pandas pillow python-dotenv pytesseract` + `scripts/requirements-ocr.txt` (RapidOCR) + binary Tesseract (nếu dùng dự phòng).
- Template **đã có**: `context/template/MauTokhai.xml`, `MauTokhaihangxuatPV.xml`, `lo_config.sumi08.example.json`, `port_pending_BL.json`.

> Cách lấp: tái sinh từ Excel nguồn (`export_dictionary_context_to_csv.py --from-source`, `convert_tariff.py`) **nếu** có file `context/dictionary/source/*.xlsx` và workbook biểu thuế — hiện cũng chưa có trong bản này.

## 7. Cấu trúc & tài liệu đáng đọc
- Rules: `.cursor/rules/{TKhai,HSCode,vietnamese-writing-rules}.mdc` · Experiences: `context/experiences/skill-*.md`
- Pipeline: `scripts/{lo_pipeline,sumi_pipeline}.py` · Build: `build_tokhai_xml_from_canonical.py` · Gate: `audit_runner.py`, `audit_rules.py`, `handover_check.py`
- Tài liệu: `docs/{ARCHITECTURE,CONFIGURATION,DATA,SETUP,RUNBOOK,TROUBLESHOOTING}.md`

---
## ✅ Việc cần làm khác đi cho BRAVO
- **Quy mô khác**: Atlas = 1 lô → 1 tờ khai (one-shot); BRAVO = giao dịch lặp lại, 1 hoá đơn → nhiều bút toán. Pattern gate giữ nguyên, nhưng state phải bền và truy vết theo giao dịch.
- **Thiếu RLS/đa người dùng**: Atlas chạy đơn người dùng theo lô. BRAVO **bắt buộc** áp RLS phòng ban/đơn vị (mượn từ arkon) lên *mọi* lookup và artifact.
- **Master khác chủ sở hữu**: Atlas master = từ điển shipper/cảng (file). BRAVO master = sổ cái ERP qua REST read-only — cần lock & xác thực quyền khi đọc.
- **Verify online thay vì batch**: gate của Atlas chạy theo lô ngoài luồng; BRAVO cần verify-gate *trong* agent loop trước khi tạo draft.
- **Giữ pattern vàng**: experiences-as-skills · routing + fail-loud · audit(cảnh báo)↔handover(chặn) · master-là-sự-thật + liệt-kê-ứng-viên · source tracking. Xem thêm [[hermes-notes]] cho mặt agent-loop/nén-ngữ-cảnh.
