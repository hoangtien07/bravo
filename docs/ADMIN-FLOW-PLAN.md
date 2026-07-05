# ADMIN-FLOW-PLAN — Luồng nghiệp vụ Quản trị (Backend + Frontend)

Kế hoạch chi tiết cho vai **Quản trị viên (admin)** của BRAVO AI Copilot: những gì ĐÃ có (Wave
1/2), luồng nghiệp vụ đầy đủ, và các GAP cần bổ sung. Mục tiêu: một admin (IT/kế toán trưởng)
tự vận hành hệ thống **không cần chạy script Python**.

> Trạng thái ký hiệu: ✅ đã làm · 🔶 một phần · ❌ gap (kế hoạch dưới). Bối cảnh: [DEPLOY-GCP.md](DEPLOY-GCP.md),
> quyền/RLS: [SECURITY-RLS.md](SECURITY-RLS.md), backend admin: `app/api/routes_admin.py`, FE: `frontend-react/src/features/admin/AdminPage.tsx`.

---

## 1. Ai là admin & phạm vi

- **Admin = `Employee.is_admin = True`** (vd `giamdoc@bravo.vn`). `is_admin` **bypass mọi RLS/permission**
  (`app/security/rls.py`, `app/agent/tools.py::_has_permission`) — thấy mọi phòng ban, mọi nháp.
- Cổng admin: dependency `require_admin` (`app/security/auth.py`) — khác `require_permission`, yêu cầu
  cứng `is_admin`. Mọi route `/api/admin/*` qua cổng này (trừ đổi mật khẩu tự phục vụ).
- FE: nav "Quản trị" chỉ hiện khi `identity.is_admin` (`ConversationSidebar.tsx`); trang `/admin`
  tự chặn nếu không phải admin.

---

## 2. Backend hiện có (✅ Wave 1/2) — `app/api/routes_admin.py`

| Method | Endpoint | Chức năng | Bảo mật |
|---|---|---|---|
| GET | `/api/admin/users` | Liệt kê user (email, họ tên, quyền, phòng ban) | require_admin |
| GET | `/api/admin/permissions` | Danh sách permission gán được (whitelist hẹp) | require_admin |
| POST | `/api/admin/users` | Tạo user (email/họ tên/mật khẩu/is_admin/perms/depts) | require_admin, validate perms |
| PATCH | `/api/admin/users/{id}` | Sửa họ tên/quyền/phòng ban/is_admin | require_admin, chống tự-hạ-admin |
| POST | `/api/admin/users/{id}/password` | Admin reset mật khẩu | require_admin |
| POST | `/api/auth/change-password` | User tự đổi mật khẩu (cần mật khẩu cũ) | get_current_identity |
| GET | `/api/admin/departments` | Liệt kê phòng ban | require_admin |
| POST | `/api/admin/departments` | Tạo phòng ban (name, sensitive) | require_admin |
| GET | `/api/admin/usage?days=N` | Token + ước phí theo người dùng (từ AgentRun) | require_admin |

**Mô hình quyền (permission):** chuỗi `{resource}:{action}:{scope}` (SECURITY-RLS §2.2). Whitelist gán
được (`ASSIGNABLE_PERMISSIONS`): `doc:read:own_dept|all`, `doc:create|:all`, `metric:read`,
`draft:create`, `draft:approve|:own_dept`. Gán perm ngoài whitelist → 422 (không cho tự chế quyền).

## 3. Frontend hiện có (✅) — `AdminPage.tsx` (`/admin`)

- **Phòng ban:** tạo phòng ban mới; hiển thị danh sách (badge cảnh báo phòng "nhạy").
- **Tạo user:** form email/họ tên/mật khẩu + checkbox admin + chọn phòng ban (multi) + chọn quyền (multi
  từ whitelist server trả về).
- **Danh sách user:** bảng email/họ tên/phòng ban/quyền + nút "Đặt mật khẩu".
- **Usage:** bảng token + ước phí 7 ngày/người (W2.4).

---

## 4. LUỒNG NGHIỆP VỤ ADMIN (chi tiết)

### 4.1 Vòng đời người dùng (User lifecycle)
```
[Tạo phòng ban] → [Tạo user + gán phòng ban + gán quyền] → [User đăng nhập, đổi mật khẩu]
   → [Sửa quyền/phòng ban khi đổi vai] → [Reset mật khẩu khi quên] → [Khoá khi nghỉ việc ❌gap]
```
- **Tạo:** admin nhập tối thiểu email + họ tên + mật khẩu (≥6). Chọn phòng ban → quyết định RLS scope
  (user chỉ thấy dữ liệu phòng mình + global). Chọn quyền từ whitelist.
- **Phân vai chuẩn (khuyến nghị seed):** *maker* = `draft:create:own_dept` (tạo nháp, KHÔNG tự duyệt);
  *checker* = thêm `draft:approve:own_dept` (duyệt nháp người khác — maker-checker). KHÔNG gán cả hai
  cho cùng người nếu muốn tách vai kiểm soát.
- **Sửa vai:** PATCH quyền/phòng ban. Guard: admin **không thể tự bỏ quyền admin của chính mình** (409)
  — tránh khoá mình ra ngoài.
- **Reset mật khẩu:** admin đặt mật khẩu mới; user tự đổi qua `/api/auth/change-password` (cần mật khẩu cũ).

### 4.2 Quản trị phòng ban & phân quyền RLS
- Phòng ban = đơn vị RLS. Cờ `sensitive` (Kế toán/Nhân sự) → ghim egress local + chỉ tiêu nhạy (lương).
- Gán user vào ≥1 phòng ban → `department_ids` → lọc `chunk_scope_filter`/`draft_scope_filter` trong SQL.
- Tài liệu/nháp KHÔNG gán phòng = **global** (mọi user đọc được). Gán phòng = chỉ phòng đó + admin.

### 4.3 Giám sát vận hành (usage/cost + governance)
- **Usage/cost (✅):** admin xem token + ước phí/người 7 ngày (`/api/admin/usage`) → phát hiện lạm dụng,
  ước chi phí LLM. Đơn giá đặt ở `settings.cost_per_1m_*`.
- **Audit trail (🔶):** `AuditLog` + `ToolCallAttempt` đã ghi (đăng nhập egress, tạo/duyệt/từ chối nháp,
  tool-call) NHƯNG **chưa có endpoint/UI xem** → gap 5.1.
- **Giám sát maker-checker (🔶):** admin thấy mọi nháp (is_admin bypass) qua trang `/drafts`, nhưng chưa
  có bộ lọc "theo người tạo/người duyệt" cho kiểm toán → gap 5.4.

### 4.4 Cấp phát tích hợp (MCP token, SSO)
- **MCP token (🔶):** hiện chỉ cấp qua seed (`mcp_token_hash`). Chưa có UI admin phát/thu hồi token cho
  Claude Desktop/Code → gap 5.2.
- **SSO/OIDC (✅ tự provisioning):** user đăng nhập SSO lần đầu → tự tạo Employee quyền tối thiểu
  (`doc:read:own_dept`, không admin). Admin sau đó gán phòng ban/quyền qua trang Quản trị. (Xem [SSO-OIDC.md](SSO-OIDC.md).)

---

## 5. GAP & KẾ HOẠCH BỔ SUNG (ưu tiên giảm dần)

### 5.1 Khoá/vô hiệu hoá tài khoản (❌ — ưu tiên CAO)
Hiện KHÔNG khoá được user (Employee không có cờ active) → nhân viên nghỉ việc vẫn đăng nhập được.
- **BE:** thêm cột `Employee.is_active: bool = True` (migration). `get_current_identity` + `login` từ chối
  nếu `not is_active` (401). Endpoint `PATCH /api/admin/users/{id}` nhận `is_active`. Xoá mềm thay xoá cứng
  (giữ FK draft/audit).
- **FE:** toggle "Kích hoạt/Khoá" ở bảng user; hàng bị khoá làm mờ.
- **Nghiệm thu:** khoá user → user đó login 401; nháp/audit cũ vẫn còn.

### 5.2 Quản lý MCP token qua UI (❌ — ưu tiên TRUNG BÌNH)
- **BE:** `POST /api/admin/users/{id}/mcp-token` sinh token ngẫu nhiên, lưu HMAC-hash, **trả plaintext MỘT
  LẦN**; `DELETE` thu hồi (xoá hash). Không bao giờ lưu/hiển thị lại plaintext.
- **FE:** nút "Cấp MCP token" → modal hiện token 1 lần + nút copy; badge "đã cấp/chưa".
- **Nghiệm thu:** token cấp nối được `/mcp`; thu hồi → 401.

### 5.3 Trang xem Audit log (❌ — ưu tiên TRUNG BÌNH, cần cho kiểm toán)
- **BE:** `GET /api/admin/audit?actor=&action=&from=&to=&limit=` đọc `AuditLog` (RLS: admin xem tất cả),
  phân trang. Kèm export CSV.
- **FE:** bảng thời gian/người/hành động/chi tiết + bộ lọc; dùng cho câu hỏi kiểm toán "ai duyệt bút toán X".
- **Nghiệm thu:** lọc theo action=`draft.approve` ra đúng lịch sử duyệt.

### 5.4 Governance nháp cho kiểm toán (🔶 → ✅)
- **BE:** `/api/drafts` thêm filter `created_by`, `approved_by`, khoảng thời gian (đã có RLS + export).
- **FE:** trang `/drafts` thêm bộ lọc người tạo/người duyệt + cột "ai duyệt, khi nào".
- **Nghiệm thu:** kế toán trưởng lọc nháp theo nhân viên + tải nhật ký duyệt.

### 5.5 Tiện ích quy mô (❌ — ưu tiên THẤP)
- **Role templates:** gán nhanh bộ quyền theo vai (Kế toán/Helpdesk/Trưởng phòng) thay vì tick từng perm.
- **Nhập user hàng loạt:** CSV import (email/họ tên/phòng ban/vai) — hữu ích khi onboard cả phòng.
- **Đổi phòng ban hàng loạt / phân trang danh sách user** khi >vài trăm user.

---

## 6. Thứ tự thực thi đề xuất

| Đợt | Việc | Lý do |
|---|---|---|
| **A1** (ngay) | 5.1 Khoá tài khoản | Bảo mật cứng — nhân viên nghỉ phải chặn được ngay |
| **A2** | 5.3 Audit log viewer + 5.4 filter drafts | Kiểm toán bút toán — điều kiện bán cho kế toán trưởng |
| **A3** | 5.2 MCP token UI | Mở khoá tích hợp Claude Desktop cho power-user |
| **A4** (khi scale) | 5.5 role template + bulk import + phân trang | Chỉ cần khi nhiều user |

Phụ thuộc: A1 cần 1 migration (thêm `is_active`); A2/A3 chỉ thêm route + trang, không migration
(AuditLog/mcp_token_hash đã có). Tất cả nằm trong kiến trúc hiện tại (require_admin + RLS-in-SQL).

---

## 7. Checklist test nội bộ (dùng tài khoản seed)

Sau `deploy/bootstrap.sh` (seed 5 tài khoản + 4 nháp mẫu), mật khẩu `demo123`:

- [ ] **giamdoc** (admin): vào `/admin` → tạo phòng ban, tạo user mới, đổi quyền, reset mật khẩu, xem Usage.
- [ ] **ketoan** (maker): `/money-engine` hoặc `/documents` upload hoá đơn → thấy nháp; vào `/drafts` thấy
      nháp của mình nhưng **KHÔNG duyệt được của chính mình** (maker-checker).
- [ ] **ketoantruong** (checker): `/drafts` → **DUYỆT** nháp của ketoan → tải Excel/CSV. Nối `/mcp` bằng
      token `bravo-mcp-demo-token`.
- [ ] **kinhdoanh** (ngoài phòng KT): `/drafts` **KHÔNG thấy** nháp phòng Kế toán (RLS); hỏi lương → từ chối.
- [ ] **nhansu** (HR): hỏi chỉ tiêu lương → trả lời (metric:read:hr); các phòng khác không thấy.
- [ ] Chat hỏi cẩm nang → trả lời **có trích dẫn trang**; hỏi ngoài corpus → từ chối.
- [ ] `/admin` với tài khoản KHÔNG admin → bị chặn (403/redirect).
