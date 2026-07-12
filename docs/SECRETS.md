# SECRETS — quản lý bí mật & xoay khoá

## Nguyên tắc
- `.env` **gitignored** (đã kiểm: `git check-ignore .env`), chưa từng vào history. Chỉ commit `.env.example` (placeholder).
- CI chạy **gitleaks** (`.github/workflows/gitleaks.yml` + `.gitleaks.toml`) mỗi push — chặn khoá lọt vào git.
- Mỗi môi trường (pilot/dev/prod) một khoá RIÊNG, có spend-limit.

## ⚠ Hành động BẮT BUỘC của người vận hành (không tự động được)
Khoá OpenAI hiện nằm plaintext trong `.env` trên đĩa và đã xuất hiện trong phiên làm việc/biên bản
→ **coi như đã lộ, phải XOAY**:

1. Vào platform.openai.com → API keys → **Revoke** khoá cũ, tạo khoá mới (pilot riêng, dev riêng), đặt **spend limit**.
2. Cập nhật `.env` (và secret của deploy, KHÔNG để trong repo) bằng khoá mới; `chmod 600 .env`.
3. Prod: nạp secret qua env-file ngoài thư mục repo hoặc Docker secrets (`docker-compose.prod.yml`), KHÔNG bind-mount `.env` từ repo.
4. Chạy `gitleaks detect --config .gitleaks.toml` một lần trên toàn history để chắc chắn sạch.

## Boot-guard
`app/config.py::validate_boot()` fail-closed ở `env in {staging,production}`: chặn khởi động nếu
`JWT_SECRET`/`MCP_TOKEN_PEPPER` còn mặc định/quá ngắn, hoặc `EGRESS_POLICY=cloud_only` mà thiếu cấu hình cloud.
