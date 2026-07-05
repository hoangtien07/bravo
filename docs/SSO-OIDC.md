# SSO / OIDC (W2.1) — đăng nhập bằng AD/LDAP qua Keycloak

Mục tiêu: doanh nghiệp đăng nhập bằng tài khoản AD/domain hiện có, không quản lý mật khẩu riêng.
Kiến trúc: **app chỉ nói OIDC** (Authlib, Authorization Code + PKCE); **Keycloak** federate LDAP/AD.
App KHÔNG tự bind LDAP → giảm bề mặt tấn công, hợp air-gap (Keycloak self-host cạnh Postgres).

```
Trình duyệt → /api/auth/oidc/login → Keycloak (login bằng AD) → /api/auth/oidc/callback
   → app map email→Employee (tạo nếu chưa có, quyền tối thiểu) → phát JWT NỘI BỘ → SPA
```

## Dựng thử (self-host)

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.keycloak.yml up -d
```

1. Vào `http://localhost:8080` (admin/admin — ĐỔI ngay).
2. Tạo **realm** `bravo`.
3. **Clients → Create**: client id `bravo`, type *confidential*, Valid redirect URIs =
   `http://localhost:8000/api/auth/oidc/callback`. Lấy **Client secret** ở tab Credentials.
4. **User Federation → Add LDAP**: trỏ tới AD/LDAP của khách (bind DN, users DN). Test connection.
5. Điền `.env`:
   ```
   OIDC_ENABLED=true
   OIDC_ISSUER=http://localhost:8080/realms/bravo
   OIDC_CLIENT_ID=bravo
   OIDC_CLIENT_SECRET=<client secret>
   OIDC_REDIRECT_URI=http://localhost:8000/api/auth/oidc/callback
   SESSION_SECRET=<chuỗi ngẫu nhiên ≥16 ký tự>
   ```
6. Khởi động lại app. Trang login hiện nút **"Đăng nhập bằng SSO (AD/LDAP)"**.

## Ghi chú bảo mật
- `boot-guard` (W2.6) chặn khởi động prod nếu `oidc_enabled=true` mà thiếu cấu hình / `session_secret` yếu.
- User tạo từ SSO nhận **quyền tối thiểu** (`doc:read:own_dept`), KHÔNG auto-admin. Admin gán phòng
  ban/quyền qua trang **Quản trị** (W1.8).
- Login mật khẩu local vẫn giữ (fallback demo / tài khoản service); tắt bằng cách không cấp mật khẩu.
- Chưa làm: SCIM auto-provisioning, map group AD → phòng ban tự động (đưa vào roadmap khi khách cần).
