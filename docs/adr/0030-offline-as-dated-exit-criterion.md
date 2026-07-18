# 0030. Hoà giải cloud-only (0019) với bất biến #4: offline là exit-criterion CÓ NGÀY + drift-guard

- **Trạng thái:** **Proposed** (2026-07-19) — chờ chủ dự án Accept. Do V2 P0.5 containment nêu ra.
- **Ngày:** 2026-07-19
- **Bối cảnh quyết định:** review kiến trúc độc lập + hội đồng (an ninh, triển khai) phát hiện mâu
  thuẫn governance: [ADR-0019](0019-cloud-only-llm-strategy.md) (Accepted) chốt cloud-only cho v2,
  trong khi CLAUDE.md nguyên tắc #4 và AGENTS.md vẫn tuyên bố offline-capable là **bất biến**. Hai
  nguồn authority phủ định nhau → mọi gate/review sau không biết fail theo tiêu chuẩn nào.
- **Liên quan:** amends cách diễn giải bất biến #4; không thay đổi #1/#2/#3;
  [ADR-0022](0022-egress-guard-to-audit.md); [docs/SECURITY-DB-BACKSTOP.md](../SECURITY-DB-BACKSTOP.md).

## Vấn đề

"Offline mặc định" là bất biến ở CLAUDE.md, nhưng thực tế pilot chạy `egress_policy=cloud_only`
([bằng chứng trong 0019](0019-cloud-only-llm-strategy.md): `.env` trỏ OpenAI, service vLLM bị
comment). Giữ nguyên hai tuyên bố trái ngược khiến: (a) không thể tuyên bố tuân thủ; (b) đường
hybrid mục âm thầm (không CI nào chạy nhánh offline) rồi "chết" khi cần bán on-prem.

## Quyết định đề xuất

**Đổi bất biến #4 từ "offline mặc định tại mọi thời điểm" thành "offline-capable là một
exit-criterion CÓ NGÀY, được bảo vệ bằng drift-guard".** Cụ thể:

1. **Pilot v2 chạy cloud-only** (giữ 0019), nhưng đây là *trạng thái tạm* có ngày kết thúc do chủ
   dự án đặt, không phải bỏ vĩnh viễn chủ quyền.
2. **`egress_policy=hybrid` là đường tái nhập bắt buộc còn sống** — giữ code router/sensitivity/
   egress-guard (0019 đã cam kết không xoá).
3. **Drift-guard (fail-loud):** thêm một CI job định kỳ boot `egress_policy=hybrid` đối một local
   endpoint nhỏ (llama.cpp/GGUF CPU hoặc mock OpenAI-compatible) và chạy test RLS + egress-guard.
   Nếu nhánh hybrid vỡ → CI đỏ, không để mục âm thầm. (Chưa implement — công việc P-sau.)
4. **Ghi rõ chi phí tái nhập:** quay lại local bge-m3 (1024-dim) từ cloud 1536-dim ⇒ **re-embed
   toàn corpus**. Exit-criterion phải kể chi phí này, không chỉ "lật config".
5. **Dữ liệu nhạy (HR/lương/kế toán/PII) ghim cứng local** bất kể policy — không tự động egress.
6. **Sign-off pháp lý PDPL/NĐ13 cross-border là launch-gate** cho cloud-only chạm dữ liệu thật
   (ngoài phạm vi code; chủ dự án + pháp chế quyết).

## Hệ quả

- **Tích cực:** một nguồn sự thật duy nhất về egress; CI bắt drift; tuyên bố tuân thủ nhất quán
  (audit-then-egress theo 0022 là chứng cứ); đường on-prem không chết lặng.
- **Tiêu cực/chi phí:** phải viết CI drift-guard; phải cập nhật CLAUDE.md #4 + AGENTS.md cho khớp
  khi ADR này Accepted.

## Việc phải làm khi Accept

- Cập nhật CLAUDE.md nguyên tắc #4 và AGENTS.md invariant offline → "exit-criterion có ngày".
- Thêm CI job hybrid drift-guard.
- Ghi ngày mục tiêu on-prem-ready vào [PROJECT-STATE.md](../PROJECT-STATE.md).

## Ghi chú liên quan (canary runtime)

V2 P0.7 đã **park** OpenAI Agents SDK canary bằng boot-guard fail-closed (nó bypass router
egress-audit + verify-gate). Điều này tạm thời **treo phần enable-by-canary của
[ADR-0027b](0027-openai-agents-runtime-migration.md)**; chỉ mở lại khi canary đi qua guard chung
(V2 P3). Cần một ADR riêng chính thức supersede 0027b nếu hướng runtime đổi hẳn.
