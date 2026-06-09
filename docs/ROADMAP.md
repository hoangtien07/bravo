# ROADMAP — BRAVO AI Copilot

> Lộ trình theo giai đoạn, ánh xạ tới giá trị & rủi ro trong [VISION.md](VISION.md). Đây là kế hoạch *định hướng*, không phải cam kết lịch — mốc thời gian chốt khi có nguồn lực & xác nhận từ BRAVO (xem VISION §8).

## Nguyên tắc lộ trình
1. **Giá trị trước, rủi ro sau:** làm tri thức (rủi ro thấp) trước khi chạm số liệu tài chính (rủi ro cao).
2. **Chứng minh được trước khi mở rộng:** mỗi giai đoạn có metric; không qua giai đoạn sau nếu chưa đạt.
3. **Mỗi tính năng lớn qua `/council-review`** trước khi xây.

---

## Giai đoạn 0 — Nền móng & Quyết định (HIỆN TẠI)
*Mục tiêu: chốt hướng đi, không code sản phẩm.*
- [x] Thiết lập Claude harness (CLAUDE.md, council, skills).
- [x] Nghiên cứu 3 repo, tổng hợp VISION/ARCHITECTURE/SECURITY.
- [ ] Trả lời các câu hỏi mở với BRAVO (VISION §8): REST API ERP, draft queue, mô hình phòng ban, phần cứng, tài liệu mẫu.
- [x] ADR-0003: chiến lược LLM = **hybrid** (local mặc định + cloud opt-in có kiểm soát).
- [ ] ADR nền tảng còn lại: vector store, kích thước Qwen + nhà cung cấp cloud, lược đồ phân loại độ nhạy, mức dùng MRP, cơ chế tích hợp ERP.
- [ ] Dựng **bộ eval** (golden Q&A tiếng Việt + corpus mẫu): **RAGAS** (faithfulness) + **Trust-Score** (từ chối đúng cách) + **benchmark masked-span kiểu FAITH trên báo cáo tài chính tiếng Việt** (đo độ chính xác số liệu). → cổng ra chất lượng. *(Cơ sở: [research/findings/B](research/findings/B-academic-technical.md).)*
- [ ] Áp **Checklist 15 điều trước khi giao khách** + 10 dấu hiệu đi chệch ([research/findings/C §7-8](research/findings/C-deployment-pitfalls.md)) làm cổng ra production.
- [ ] (BRAVO) Nhờ pháp chế xác nhận đòn bẩy pháp lý ([research/findings/E](research/findings/E-vietnam-legal.md)); khảo sát hành vi mua + mức sẵn-lòng-trả VN.
- **Cổng ra:** có ADR nền + bộ eval + xác nhận hạ tầng từ BRAVO.

## Giai đoạn 1 — MVP: Cổng Tri thức & Vận hành
*Giá trị: giảm tải helpdesk, rút ngắn bàn giao. Rủi ro: thấp (không chạm số liệu tài chính).*

**1A. Ingestion + RAG có trích dẫn**
- Nạp PDF/DOCX/XLSX qua Docling; mở rộng provenance (trang/sheet/ô).
- Vector store + embedding cục bộ; retrieval lọc scope ở SQL.
- **Model Router** (local mặc định) + phân loại độ nhạy cơ bản; cloud TẮT ở MVP, hạ tầng router sẵn sàng để bật sau.
- Trả lời kèm trích dẫn nguồn.

**1B. RLS + xác thực**
- Phân quyền phòng ban ở tầng SQL; đăng nhập; audit log.
- Skill `/rls-check` xanh cho mọi đường dữ liệu.

**1C. Giao diện hỏi-đáp + MCP**
- Web UI hỏi-đáp; (tuỳ chọn) MCP cho Claude Desktop nội bộ.
- Hai use-case đầu: tra cứu quy chế/định khoản (kế toán/HR) & cẩm nang triển khai/mã lỗi (kỹ thuật).

- **Metric cổng ra:** citation accuracy ≥ 95%; ≥ 30–40% câu helpdesk tự phục vụ; 0 rò scope trong pen-test nội bộ; pilot 1 phòng ban hài lòng.

## Giai đoạn 2 — Agent & Tích hợp ERP (đọc)
*Giá trị: hỏi-đáp số liệu tự phục vụ. Rủi ro: trung bình–cao (chạm số liệu → guardrail nghiêm).*

**2A. Lõi agent có bộ nhớ (letta pattern)** — core/archival/recall; quản lý context window cho LLM cục bộ.
**2B. ERP read tools (read-only)** — gọi REST/view đã duyệt; lọc scope+đơn vị+kỳ; luôn trả bản ghi nguồn.
**2C. Hỏi-đáp số liệu NL (VISION §5.2.A)** — guardrail: trích nguồn, drill-down, nhãn "cần xác nhận".

- **Metric cổng ra:** độ chính xác số liệu trên bộ eval tài chính ≥ ngưỡng đặt ra; thời gian câu-hỏi→insight giảm rõ; kế toán xác nhận tin dùng.

## Giai đoạn 3 — Phân tích chủ động & Draft automation
*Giá trị cao cho CFO/kiểm soát. Rủi ro: cao → kiểm soát chặt + human-in-the-loop.*
- **3A. Phát hiện bất thường & rủi ro** (VISION §5.2.B) — agent nền theo lịch, cảnh báo có dẫn chứng.
- **3B. Soạn nháp chứng từ/định khoản** (VISION §5.2.C) — draft cân nợ-có vào hàng đợi ERP.
- **3C. Báo cáo quản trị NL** (VISION §5.2.D).
- **Metric:** % nháp duyệt không sửa; số cờ rủi ro hợp lệ phát hiện sớm.

## Giai đoạn 4 — Đóng gói thương mại (add-on)
- Helm chart / installer cho đội triển khai BRAVO cài tại site khách (vài giờ).
- Cấu hình theo khách (phòng ban, model, tài nguyên) tách khỏi code.
- Định giá & gói bán (theo user/site/tính năng); tài liệu bán hàng & demo.
- **Suy luận liên-tài-liệu** (VISION §5.2.E) như tính năng cao cấp khác biệt.

---

## Bảng tóm tắt giá-trị / rủi-ro
| GĐ | Trọng tâm | Giá trị | Rủi ro | Chạm số liệu? |
|----|-----------|---------|--------|---------------|
| 0 | Nền móng | — | — | Không |
| 1 | Tri thức/vận hành | Cao, nhanh | Thấp | Không |
| 2 | Hỏi-đáp ERP | Rất cao | TB–Cao | Có (đọc) |
| 3 | Chủ động + draft | Rất cao | Cao | Có (draft) |
| 4 | Thương mại hoá | Doanh thu | TB | — |

## Phụ thuộc & điều kiện
- GĐ2+ phụ thuộc **REST API Read-Only của BRAVO ERP** sẵn sàng & đủ phủ.
- GĐ3 phụ thuộc **hàng đợi staging/draft** trên giao diện ERP.
- Mọi giai đoạn phụ thuộc **hạ tầng offline** (GPU/CPU) tại khách — xác nhận sớm ở GĐ0.
