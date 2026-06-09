# SECURITY & ROW-LEVEL SECURITY — BRAVO AI Copilot

> Mô hình bảo mật, kế thừa nguyên mẫu RLS của arkon. Đây là tài liệu nền cho agent `security-rls-auditor` và skill `/rls-check`. Nguyên tắc gốc: [VISION.md §2](VISION.md).

## 1. Tín điều
> **Một dòng dữ liệu chỉ rời khỏi cơ sở dữ liệu nếu identity của người yêu cầu được phép thấy nó — và việc kiểm tra đó xảy ra TRONG câu truy vấn SQL, không phải sau đó.**

Lọc trong bộ nhớ ứng dụng là *phản pattern* — một bug quên-lọc là một vụ rò dữ liệu. RLS ở tầng SQL biến "an toàn" thành mặc định.

## 2. Mô hình phân quyền (kế thừa Arkon dual-realm)

### 2.1 Định danh & phòng ban
- **Employee** ↔ **Department**: quan hệ nhiều-nhiều. `employee.department_ids` = tập phòng ban được gán.
- Nhân viên không thuộc phòng nào ⇒ chỉ thấy tài nguyên **dùng chung (global)**.

### 2.2 Quyền (permission) — định dạng `{resource}:{action}:{scope}`
- `resource` ∈ {`doc`, `erp`, `analytics`, `draft`, `admin`, ...}
- `action` ∈ {`read`, `create`, `edit`, `delete`, `approve`, ...}
- `scope` ∈ {`own_dept`, `all`} — `own_dept` = phòng ban của mình + tài nguyên global; `all` = không giới hạn.

### 2.3 Gắn nhãn tài nguyên
- **Tài liệu / chunk / bản ghi** gắn 0..n `department_id`.
- **0 phòng ban = global** (mọi người có quyền `read` đều thấy).
- **n phòng ban = OR scope** (thành viên của *bất kỳ* phòng nào trong đó thấy được).
- Với phân tích ERP: scope thêm chiều **đơn vị cơ sở / kỳ kế toán** khi áp dụng.

## 3. Điểm cưỡng chế (enforcement points)

Mọi đường dữ liệu phải áp scope **trong SQL**. Bảng các đường và cách áp:

| Đường truy cập | Cưỡng chế thế nào |
|----------------|-------------------|
| REST API (list/detail) | `require_permission` + `build_*_filter` dựng WHERE theo `department_ids` |
| RAG vector search | điều kiện `source_id IN (allowed)` / `department_id IN (...)` **ghép vào truy vấn vector**, không lọc top-k sau |
| MCP tools | token → `ResolvedIdentity` (scope) → mỗi tool `apply_scope_filter` |
| ERP read tools | truyền scope (phòng ban/đơn vị/kỳ) xuống tham số API; chỉ gọi view đã duyệt |
| Citations/preview | đoạn trích chỉ lấy từ chunk đã qua scope filter |
| Draft queue/notifications | key theo identity; không trộn scope |

## 4. Quy tắc lộ thông tin "out-of-scope" (chống suy luận)
Khi người dùng chạm tài nguyên tồn tại nhưng ngoài quyền:
- ✅ Được phép lộ: **loại scope + số lượng** (vd "3 tài liệu thuộc phòng HR — liên hệ quản trị HR").
- ❌ Tuyệt đối KHÔNG lộ: tiêu đề, tóm tắt, nội dung, hay metadata nhạy cảm (tên tài liệu có thể chính là bí mật, vd "Kế hoạch cắt giảm Q1").

## 5. Token & xác thực
- Token MCP/API lưu **hash HMAC-SHA256 + pepper** (pepper đặt lúc deploy, không lưu DB). Plaintext chỉ hiện một lần khi tạo.
- DB bị lộ mà không có pepper ⇒ không giả mạo được token.
- Scope của token = scope của employee tại thời điểm resolve. Hỗ trợ thu hồi/xoay vòng.

## 6. Tuân thủ pháp lý Việt Nam
- **Luật Bảo vệ Dữ liệu Cá nhân 91/2025/QH15 (Điều 20, hiệu lực 1/1/2026, thay NĐ 13/2023 + NĐ 356/2025):** lưu/xử lý dữ liệu cá nhân **khách hàng/đối tác** (công dân VN) trên cloud **nước ngoài** = *chuyển dữ liệu xuyên biên giới* → **hồ sơ CTIA** nộp Cục An ninh mạng (A05) trong 60 ngày; phạt tới **3 tỷ/5% doanh thu**. **On-prem né được lớp này.** *(Đã re-verify vs văn bản gốc — [research/findings/F §0-1](research/findings/F-reverification.md).)*
  - ⚠️ **Đính chính (đã xác minh):** Khoản 6 Điều 20 **MIỄN** cho dữ liệu cá nhân của **chính nhân viên** lên cloud → đòn bẩy này **KHÔNG áp dụng cho HR/lương nội bộ**, chỉ cho dữ liệu khách hàng/nghiệp vụ.
  - ⚠️ **DPIA** (Điều 21) áp dụng **mọi** bên kể cả on-prem → on-prem *giảm* chứ không *xoá* tuân thủ. Nội địa hoá (NĐ 53/2022) & Luật Dữ liệu 60/2024 **không** tạo đòn bẩy on-prem cho dữ liệu nghiệp vụ thường. Số điều mẫu NĐ 356/2025 cần luật sư BRAVO xác nhận.
- **Audit log:** ghi mọi truy cập đặc quyền & mọi lần tạo/duyệt draft (ai, khi nào, cái gì) phục vụ thanh tra.
- **Lưu trú dữ liệu:** ở cấu hình offline (mặc định), dữ liệu không rời lãnh thổ/khách hàng — lợi thế tuân thủ. Khi bật hybrid, chính sách egress (§9) đảm bảo dữ liệu cá nhân/nhạy cảm vẫn không rời mạng.

## 7. Bản ghi nháp = ranh giới ghi duy nhất
- AI **không có** đường ghi trực tiếp tới SQL Server ERP. Quyền tối đa của chiều ghi = **tạo draft**.
- Duyệt draft dùng **advisory-lock** (như arkon) chống race; mọi duyệt tạo bản ghi lịch sử bất biến.
- Tôn trọng quy tắc nghiệp vụ: kỳ đã khoá sổ / chứng từ đã duyệt → không tạo draft sửa.

## 8. Checklist trước khi triển khai bất kỳ tính năng chạm dữ liệu
Chạy skill `/rls-check`. Tóm tắt:
- [ ] Liệt kê *mọi* đường dữ liệu của tính năng.
- [ ] Mỗi đường: filter scope nằm trong SQL? (không lọc sau khi nạp RAM)
- [ ] Vector search có kèm scope trong truy vấn?
- [ ] Citation/preview/error không lộ nội dung ngoài quyền?
- [ ] Tài liệu global vs giới hạn gắn nhãn đúng?
- [ ] Có audit log cho truy cập đặc quyền?
- [ ] (Nếu ghi) chỉ tạo draft, không chạm ERP gốc?
- [ ] (Nếu có gọi LLM) ngữ cảnh gửi đi có thể chứa dữ liệu nhạy? Nếu có → bắt buộc đi model local (xem §9)?

## 9. Chính sách phát tán dữ liệu ra cloud (Hybrid / data-egress) — [ADR-0003](adr/0003-hybrid-llm-strategy.md)

> RLS bảo vệ dữ liệu *trong* hệ thống. Khi bật cloud (hybrid), xuất hiện một biên mới: **dữ liệu rời mạng nội bộ** trong prompt gửi tới LLM ngoài. Đây là bề mặt tấn công riêng — phải kiểm soát ngang RLS.

### 9.1 Tín điều egress
> **Mặc định không gì rời mạng. Một mẩu dữ liệu chỉ được gửi tới model cloud nếu: (a) khách đã chủ động bật cloud, VÀ (b) lớp dữ liệu đó được chính sách whitelist cho phép egress, VÀ (c) nó không mang nhãn nhạy cảm. Thiếu bất kỳ điều kiện nào ⇒ chạy local.**

### 9.2 Model Router — điểm cưỡng chế egress
Mọi lời gọi LLM đi qua **Model Router**. Router quyết định local-vs-cloud dựa trên:
1. **Cấu hình triển khai:** cloud bật/tắt (mặc định TẮT); danh sách nhà cung cấp cho phép; lớp dữ liệu nào được egress.
2. **Độ nhạy của ngữ cảnh:** tính từ nhãn nguồn dữ liệu (tái dùng `department_id` + `knowledge_type` của RLS) của *mọi* chunk/bản ghi đưa vào prompt. Prompt nhạy = bất kỳ thành phần nào nhạy.
3. **Loại tác vụ.**

**Fail-closed:** không xác định được độ nhạy ⇒ coi là nhạy ⇒ chạy local. Lỗi router ⇒ local. Không bao giờ "mở khi nghi ngờ".

### 9.3 Phân loại độ nhạy (sensitivity classification)
- Gắn nhãn độ nhạy cho tài liệu/dữ liệu **ngay khi nạp** (ingestion) và cho dữ liệu ERP theo loại tài khoản/bảng.
- Lớp mặc định **NHẠY (local-only)**: số liệu kế toán/tài chính, lương, HR, hợp đồng, mọi dữ liệu cá nhân (PII theo Nghị định 13/2023).
- Lớp có thể **whitelist egress**: tài liệu kỹ thuật công khai (cẩm nang triển khai, mã lỗi, tham số cấu hình) — và chỉ khi admin bật.
- Quy tắc kế thừa RLS: dữ liệu gắn phòng ban nhạy (Kế toán/HR) ⇒ nhạy; tài liệu global kỹ thuật ⇒ có thể whitelist.

### 9.4 Phòng vệ bổ sung
- **Audit egress:** ghi mọi lời gọi cloud — lớp dữ liệu, nhà cung cấp, người dùng, thời điểm, hash prompt. Phục vụ thanh tra.
- **Redaction PII (tuỳ chọn bật):** khử nhận dạng trước khi gọi cloud cho lớp được phép.
- **Cô lập theo khách:** policy egress cấu hình per-deployment, tách khỏi code.
- **Đồng bộ với RLS:** một người dùng không được "lách" bằng cách hỏi qua cloud thứ họ không có quyền đọc — router chạy *sau* RLS, chỉ thấy dữ liệu đã trong scope của người hỏi.

### 9.5 Checklist egress (thêm vào `/rls-check` khi cloud bật)
- [ ] Cloud đang TẮT theo mặc định?
- [ ] Mọi ngữ cảnh prompt có được tính độ nhạy từ nhãn nguồn?
- [ ] Dữ liệu nhạy (kế toán/lương/HR/PII) ghim cứng local kể cả khi cloud bật?
- [ ] Router fail-closed (không rõ ⇒ local)?
- [ ] Mọi lời gọi cloud được audit?
- [ ] Policy egress tách khỏi code, cấu hình per-khách?

## 10. Phòng thủ prompt-injection (RAG ingest tài liệu)

> Bằng chứng (Track C): sự cố thật **Slack AI** (rò dữ liệu private channel) và **M365 Copilot / EchoLeak** (CVE-2025-32711, CVSS 9.3, exfil qua ASCII smuggling); **OWASP LLM01:2025** xác nhận *RAG/fine-tuning KHÔNG khử được prompt injection*. Vì BRAVO ingest PDF/DOCX/Excel do người dùng tải lên, đây là bề mặt tấn công **không thể khử ở tầng model** → phòng thủ ở **kiến trúc**.

- **Tài liệu = nội dung KHÔNG tin cậy.** Nội dung tài liệu/chunk retrieve về **không bao giờ** được coi là chỉ thị; tách bạch rõ system prompt vs context (đóng khung, gắn nhãn nguồn).
- **Scoped retrieval (đúng lỗi Slack):** RAG chỉ kéo chunk **trong scope quyền** của người hỏi (RLS ở SQL) — không bao giờ đưa dữ liệu ngoài quyền vào context.
- **Cắt chuỗi exfiltration:** không tự động render link/ảnh từ nội dung không tin cậy; chống ký tự ẩn (ASCII/Unicode smuggling) trong output; agent ghi = **nháp chờ duyệt** (không auto-execute tool → không tự gọi tool tìm thêm dữ liệu nhạy).
- **Giới hạn agency:** tool rules (học letta) cưỡng chế agent chỉ gọi tool đọc đã duyệt; mọi tool ghi `requires_approval`.

## 11. Tham chiếu cài đặt gốc (arkon)
- `../arkon/app/services/permission_engine.py` — `build_document_filter`, `can_access_document`
- `../arkon/app/services/mcp_auth_service.py` — `ResolvedIdentity`, `apply_scope_filter`, hash token
- `../arkon/app/services/permissions.py` — hằng số quyền, map vai trò
- `../arkon/app/mcp/middleware.py` — lọc danh sách tool theo quyền
- `../arkon/docs/ACCESS-CONTROL.md` — tài liệu RBAC gốc
