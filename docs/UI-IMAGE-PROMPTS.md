# BRAVO Agent AI — Image-generation prompts cho UI mockups

> Mục đích: dán vào một AI sinh ảnh (GPT image / Sora / "gpt 5.6 sol") để tạo ảnh mockup UI các màn.
> Nguồn thiết kế: [DESIGN.md](../DESIGN.md). Đã qua hội đồng 5 chuyên gia (product / RAG / security-RLS / kế toán / FE inventory) — 2026-07-19.
>
> **Cách dùng:** dán **§0 MASTER STYLE BLOCK** trước, rồi nối tiếp prompt của MỘT màn (mỗi ảnh sinh một màn). Image model dễ "loạn chữ" khi text dày → mỗi màn chỉ ghi CHÍNH XÁC vài nhãn quan trọng, phần thân để model tự điền "realistic simplified Vietnamese UI text".
>
> Thứ tự ưu tiên demo (hội đồng product): **2 → 3 → 4 → 5 → 1**, rồi frontier **F, G**. Màn H/I/J là optional.

---

## §0. MASTER STYLE BLOCK (dán trước MỌI prompt màn)

```
A high-fidelity UI mockup screenshot of an enterprise web application, desktop web, 16:10 landscape, ~1440px wide, pixel-crisp, flat vector UI (not a photo, no device frame, no browser chrome, no hands, no 3D).

PRODUCT: "Bravo Agent AI" — a trusted Vietnamese ERP accounting advisory workspace ("Trợ lý nghiệp vụ có bằng chứng"). Audience: professional accountants. Tone: calm, precise, dependable, quietly optimistic. NOT a generic AI chatbot.

VISUAL SYSTEM (follow exactly):
- Colors: brand green #00A88D (verified accents, logo area), interactive teal #006B5D (primary buttons, links, focus), hover #00574C, soft teal #E8F7F4 (selected/verified surface), canvas background #F6F9F8, white #FFFFFF cards, strong text #1F2927, secondary text #56625F, borders #D7E1DE, orange #FBAF3F + warning surface #FFF4DE (missing/pending evidence — keep under 50% of frame), error red #B42318 + error surface #FDECEA (conflict only), info blue #175CD3.
- Green dominates; orange only for attention; NEVER purple/blue neon gradients, NEVER glassmorphism, NEVER glow.
- Typography: clean system sans-serif (SF Pro / Segoe UI style), sentence case, tabular numerals for all money/dates/counts. No serif, no futuristic display font.
- Layout: subtle 1px borders instead of heavy shadows; card radius 8px, button radius 6px; generous whitespace on 8/12/16/24px rhythm; left sidebar 264px; readable content column 760–840px; optional right panel 360–400px.
- Brand signature: a paired diagonal double-slash "//" mark tilted ~29°, used sparingly as a progress/verified marker or separator — NOT as repeated background decoration.
- Status is ALWAYS shown by a text label + small icon, never by color alone.
- Language: Vietnamese UI text throughout (sentence case).

HEADER SCOPE BAR (top of every in-app screen): show working scope — "Công ty TNHH DEMO ABC · Chi nhánh Hà Nội · Kỳ 06/2026 · BRAVO 8.0". If a scope value were unknown it must read "chưa xác định" (never invented).

SAFE DEMO DATA: obviously fake — company "Công ty TNHH DEMO ABC", person "Nguyễn Văn A", period "06/2026", round amounts (1.000.000, 2.500.000, 12.500.000) formatted Vietnamese style with dots. A small subtle corner tag reads "DỮ LIỆU MẪU". No real tax codes, no real bank accounts, no fake charts, no decorative giant KPI numbers.

STRICTLY AVOID: robots, brains, faces, animals, sparkles/stars, AI-orb imagery; purple/neon gradients; glassmorphism; excessive rounded pills; fake charts; decorative citations; unexplained readiness percentages; donut/gauge charts; showing an approved action as already "executed"; showing greyed-out items the user is not allowed to see.
```

---

## §1. Sign in — màn 9.1

```
[MASTER STYLE BLOCK], then:

Screen: SIGN IN. Restrained two-column desktop layout on canvas #F6F9F8.
LEFT column (~55%, white or very light): official-style BRAVO green wordmark top-left with the product label "Agent AI" beside it as plain text; a short product thesis headline "Trợ lý nghiệp vụ có bằng chứng"; one subheadline "Quản trị chắc chắn — mọi số liệu đều có nguồn."; a single tasteful "//" mark at 29° in green. No stock photo, no illustration of people or robots.
RIGHT column (~45%): a compact white authentication card with 1px border. Primary teal (#006B5D) button "Đăng nhập bằng SSO (AD/LDAP)". Below a subtle divider "hoặc", an email field labeled "Email" and password field labeled "Mật khẩu", and a secondary outline button "Đăng nhập". Below the card, small secondary-text environment/support line: "Môi trường nội bộ · Hỗ trợ: it@demo.vn".
No shadows-heavy cards; calm and professional.
```

---

## §2. New conversation — màn 9.2 (điểm mở đầu demo)

```
[MASTER STYLE BLOCK], then:

Screen: NEW CONVERSATION (first useful task). Three-region desktop shell.
LEFT SIDEBAR (264px, white, 1px right border): top button teal "Hội thoại mới"; nav list with small icons and labels in this order: "Financial Close" (selected, soft-teal #E8F7F4 highlight + a small green "//" marker), "Hội thoại", "Kho tri thức", "Phê duyệt", "Quản trị". Bottom: user row "Nguyễn Văn A", a logout icon, and a light/dark toggle.
CENTER (canvas, content max 800px, centered): a role-aware greeting heading "Bravo Agent AI có thể hỗ trợ anh/chị kiểm tra công việc nào?"; a prominent composer input with placeholder "Nhập yêu cầu nghiệp vụ...", an attach (paperclip) icon, and a profile selector chip reading "Hồ sơ: Tự động". Below the composer, FOUR task-starter cards (2×2 grid, white, 1px border, radius 8px, subtle), each one short line:
  1. "Kiểm tra mức độ sẵn sàng đóng kỳ tháng 06/2026"
  2. "Tôi còn thiếu bước nào trước khi lập báo cáo tài chính?"
  3. "Đối chiếu các chênh lệch công nợ cuối kỳ"
  4. "Tổng hợp bằng chứng để bàn giao cho kế toán trưởng"
Below the starters, a "Hội thoại gần đây" list with 3 muted rows. A small persistent note in secondary text: "Mọi kết luận có số liệu đều kèm nguồn · Mọi thay đổi chỉ ở dạng bản nháp chờ duyệt."
Top header scope bar as specified.
```

---

## §3. Active advisory conversation + Evidence drawer — màn 9.3 + 9.5 (MÀN CHỦ LỰC)

```
[MASTER STYLE BLOCK], then:

Screen: ACTIVE ADVISORY CONVERSATION with EVIDENCE DRAWER open. Four regions: left sidebar (264px, same nav as new-conversation, "Financial Close" selected), center conversation column (~760px), right evidence drawer (~380px, white, 1px left border). Header scope bar on top: "Công ty TNHH DEMO ABC · Kỳ 06/2026 · BRAVO 8.0". Task title in header: "Sẵn sàng đóng kỳ 06/2026".

CENTER conversation:
- A user message bubble (right/neutral): "Kỳ 06/2026 đã sẵn sàng khóa chưa?"
- An assistant answer organized as labeled sections (NOT chain-of-thought): 
   Section "Kết luận": "Kỳ 06/2026 CHƯA sẵn sàng để khóa — còn 2 điểm cần xử lý."
   Section "Điều kiện còn thiếu": two lines, each with an inline numbered citation chip:
     • "Chênh lệch công nợ phải thu 12.500.000 đ" + a green badge "đã xác minh" + chip "[1]"
     • "Chưa đánh giá lại số dư ngoại tệ TK 1122" + an orange badge "thiếu bằng chứng" + chip "[2]"
   Section "Hành động đề xuất": "Đối chiếu công nợ TK 131 trước, sau đó lập bút toán đánh giá lại tỷ giá TK 413."
   A small muted disclaimer line: "Tư vấn quy trình dựa trên bằng chứng trích dẫn — chưa tính toán lại ledger."
- Numbers are bold ONLY when they carry a "đã xác minh" chip.
- Bottom composer with attach icon, a "Hồ sơ: Tự động" chip, a "Độ sâu: Thường" chip, and a small tag "Bản nháp · chưa thực hiện".

RIGHT EVIDENCE DRAWER titled "Dẫn chứng". Two evidence cards, each showing full provenance as a pill + fields:
  [1] claim "Công nợ phải thu 12.500.000 đ" — nguồn "Sổ chi tiết TK 131" · "kỳ 06/2026 · dòng 47" · trạng thái green "đã xác minh".
  [2] claim "Số dư ngoại tệ 4.200 USD" — nguồn "Bảng số dư ngoại tệ" · "ô D12" · trạng thái orange "thiếu đánh giá lại".
Each card lists: nguồn, vị trí (trang/ô/dòng), công ty/kỳ/phiên bản, trạng thái bằng chứng. Use text labels + icons to distinguish verified (green) vs missing (orange). One small "//" 29° marker on the verified card as a completion cue.
```

---

## §4. Financial Close readiness — màn 9.4 (MÀN CHỦ LỰC, đã hiệu chỉnh theo nghiệp vụ VN)

```
[MASTER STYLE BLOCK], then:

Screen: FINANCIAL CLOSE READINESS. Left sidebar (264px, "Financial Close" selected). Center: a vertical "Evidence Rail" stepper — a governed checklist of close steps, top-to-bottom, connected by a thin vertical line with paired "//" 29° markers advancing between VERIFIED steps. Header scope bar + task title "Mức độ sẵn sàng đóng kỳ 06/2026". Right side: a 360px detail panel for the selected step.

This is an AUDIT CHECKLIST, NOT a dashboard: NO percentages, NO donut/gauge, NO big KPI numbers.

Ten steps, each row = status icon + Vietnamese label + one-line reason + a small evidence count (e.g. "3/3 bằng chứng"), NOT a percentage:
1. "Phạm vi & kỳ báo cáo" — Sẵn sàng (green check) — "Kỳ 06/2026, 1 đơn vị"
2. "Chứng từ đã hạch toán" — Sẵn sàng (green) — "128/128 chứng từ đã ghi"
3. "Chốt cut-off chứng từ" — Đang xử lý (blue) — "2 chứng từ chờ xác nhận ngày"
4. "Đối chiếu sổ chi tiết ↔ sổ cái" — Xung đột (red) — "TK 131 lệch 12.500.000 đ"
5. "Xử lý cuối kỳ (khấu hao / phân bổ CCDC / đánh giá lại ngoại tệ)" — Thiếu bằng chứng (orange) — "Chưa đánh giá lại TK 1122"
6. "Bút toán kết chuyển & xác định KQKD (911)" — Chưa đánh giá (grey outline) — "Chưa kiểm tra"
7. "Kiểm soát khóa sổ" — Chưa đánh giá (grey) — "Chưa kiểm tra"
8. "Ánh xạ báo cáo & số dư đầu kỳ" — Chưa đánh giá (grey) — "Chưa kiểm tra"
9. "Báo cáo & soát xét biến động" — Chưa đánh giá (grey) — "Chưa kiểm tra"
10. "Khóa kỳ" — Không áp dụng (dimmed) — "Chờ hoàn tất các bước trên"

Status legend row (label + icon, not color-only): "Chưa đánh giá · Thiếu bằng chứng · Đang xử lý · Sẵn sàng · Xung đột · Không áp dụng".

RIGHT DETAIL PANEL (for selected step 4 "Đối chiếu sổ chi tiết ↔ sổ cái", conflict): title, reason "Chênh lệch 12.500.000 đ giữa sổ chi tiết công nợ và sổ cái TK 131", an evidence link "Sổ cái TK 131 · kỳ 06/2026 · dòng 47", responsible role "Kế toán công nợ", and a teal button "Mở dẫn chứng". Red is used only for this confirmed conflict.
```

---

## §5. Draft & approval review — màn 9.6 (bất biến #2: Approved ≠ Executed)

```
[MASTER STYLE BLOCK], then:

Screen: DRAFT & APPROVAL REVIEW (maker-checker). Left sidebar ("Phê duyệt" selected). Center: a review panel for one draft journal entry. A FIXED banner at top of the panel, soft-teal/neutral (not alarming): "Đây là bản nháp — chưa được thực hiện trên hệ thống."

Panel contents, stacked:
- Title "Bút toán đánh giá lại số dư ngoại tệ TK 1122 — kỳ 06/2026" and business purpose line "Ghi nhận chênh lệch tỷ giá cuối kỳ theo TT200/TT99."
- Affected scope: "Công ty TNHH DEMO ABC · Kỳ 06/2026 · Sổ cái TK 1122, 413".
- A journal-entry table with tabular numerals, columns "Tài khoản | Diễn giải | Nợ | Có":
    "1122 | Đánh giá lại số dư ngoại tệ | 2.500.000 | "
    "413  | Chênh lệch tỷ giá         |          | 2.500.000"
  Footer row "Tổng: Nợ 2.500.000 = Có 2.500.000" with a small green badge "Cân Nợ = Có".
- A "Trước / Sau" before-after mini comparison (two small neutral columns), no fake chart.
- Evidence & validation status: green badge "Đã xác minh chứng từ", orange note "Thiếu: xác nhận tỷ giá cuối kỳ".
- Maker / checker row: "Người lập: Trần Thị B" and "Người duyệt: Nguyễn Văn A" (two DIFFERENT people).
- Action buttons: primary teal "Phê duyệt", outline "Yêu cầu bổ sung", ghost/red-outline "Từ chối".
- A small audit trail list below: timestamped rows "08:12 — Lập bản nháp (Trần Thị B)", "08:20 — Gửi duyệt".
IMPORTANT label wording after-approval concept: an inactive helper text reads "Sau khi duyệt: 'Bản nháp đã được phê duyệt — chờ ghi vào ERP' (không phải 'Đã hoàn tất')."
```

---

## §F. Agent working / progress state — bổ sung frontier (agent quan sát được, KHÔNG lộ chain-of-thought)

```
[MASTER STYLE BLOCK], then:

Screen: same conversation layout as §3 but the assistant is CURRENTLY WORKING (in-progress state). Center column shows the user message "Kỳ 06/2026 đã sẵn sàng khóa chưa?" then an in-progress assistant block:
- A calm status line with a small spinner: "Bravo Agent AI đang đối chiếu điều kiện và bằng chứng..."
- A short vertical list of HIGH-LEVEL action steps (describe actions, NOT reasoning), each a checkable row:
    ✓ "Đã truy hồi sổ cái kỳ 06/2026"
    ✓ "Đã đối chiếu 2 nguồn công nợ"
    ⟳ "Đang kiểm tra cân Nợ = Có" (active)
    ○ "Tổng hợp kết luận" (pending)
- An ephemeral breadcrumb row of small document chips being scanned: "Sổ cái 131", "Bảng số dư ngoại tệ".
- Empty citation slots shown as skeleton placeholders "[ ]" that will fill with real chips.
Do NOT show token-by-token thinking or "I think..." text. Right evidence drawer shows one card already filled and one still loading (skeleton). Composer has a "Dừng" (stop) button visible.
```

---

## §G. Before / after ROI — bổ sung frontier (slide thuyết phục lãnh đạo, TRÌNH BÀY trung thực)

```
[MASTER STYLE BLOCK], then:

Screen: an executive comparison view "Đóng kỳ 06/2026 — Trước và sau khi dùng Bravo Agent AI". Restrained, honest, evidence-style — NO fake charts, NO giant decorative KPI numbers, NO gauges. Use a simple two-column comparison TABLE, white card, 1px border.
Columns: "Trước (thủ công)" vs "Sau (có Bravo Agent AI)". Rows (tabular numerals):
  - "Thời gian rà soát điều kiện đóng kỳ" — "≈ 6 giờ" → "≈ 1,5 giờ"
  - "Số bước tra cứu thủ công" — "24 bước" → "8 bước có bằng chứng"
  - "Chênh lệch phát hiện trước khi khóa" — "phát hiện muộn" → "cảnh báo sớm 2 điểm"
  - "Truy vết nguồn số liệu" — "thủ công" → "tự động, có trang/ô"
A small footnote in secondary text: "Số liệu minh họa nội bộ — DỮ LIỆU MẪU, chưa phải kết quả đo pilot." Keep green as the dominant accent; do not invent statistics as if measured.
```

---

## §H. Knowledge library — màn 9.7 (optional)

```
[MASTER STYLE BLOCK], then:

Screen: KNOWLEDGE LIBRARY ("Kho tri thức" selected in sidebar). Center: three tabs "Của tôi · Phòng ban · Toàn công ty". A dashed upload card "Tải tài liệu lên" with a visibility selector "Phạm vi: Phòng ban". Below, a governed document TABLE, columns: "Tên tài liệu | Chủ sở hữu | Phiên bản BRAVO | Ngày hiệu lực | Trạng thái duyệt | Phạm vi | Nạp". Rows with text+icon status badges:
  "Hướng dẫn đóng kỳ TT99.pdf | Phòng KT | BRAVO 8.0 | 01/01/2026 | Đã duyệt (green) | Toàn công ty | Đã nạp (green)"
  "Quy trình đối chiếu công nợ.docx | Nguyễn Văn A | BRAVO 8.0 | 06/2026 | Chờ duyệt (orange) | Phòng ban | Đang nạp"
  "Chính sách khấu hao (bản cũ).pdf | Phòng KT | BRAVO 7.5 | 2024 | Đã thay thế (grey) | Toàn công ty | Đã nạp"
Show page/cell traceability hint and a "Đã thay thế / mâu thuẫn" warning row. Items outside the user's scope simply DO NOT appear (never greyed-out, never a count of hidden items).
```

---

## §I. Financial Close Evidence Graph — màn 9.8 (optional)

```
[MASTER STYLE BLOCK], then:

Screen: FINANCIAL CLOSE EVIDENCE GRAPH — a GOVERNED, STABLE, left-to-right dependency map (NOT a decorative force-directed cloud, NOT glowing nodes). Flow left→right: Outcome → prerequisite groups → BRAVO operation/control → evidence. Rectangular labeled nodes connected by clean orthogonal edges; paired "//" 29° marks as directional edge markers on verified paths.
Node types with text labels + icons:
  - Outcome node (left): "Đóng kỳ 06/2026"
  - Prerequisite nodes: "Đối chiếu công nợ", "Đánh giá lại ngoại tệ", "Kết chuyển 911"
  - Operation/control nodes: "Bút toán TK 413", "Kiểm soát khóa sổ"
  - Evidence nodes (right): "Sổ cái TK 131 · dòng 47", "Bảng số dư ngoại tệ · ô D12"
  - One Conflict node (red): "Lệch 12.500.000 đ"
  - One Missing node (orange): "Thiếu đánh giá lại tỷ giá"
Green = verified path, orange = pending/missing, red = confirmed conflict. Include ONE neutral anonymous "permission boundary" placeholder where a path is not authorized — an unlabeled greyed node with NO title/count/metadata (never reveal hidden labels). Right side: a detail inspector for the selected node showing reason, evidence, kỳ, and responsible role. Toolbar: "Tìm kiếm", "Lọc", "Thu phóng", "Xem dạng danh sách". Curated fixed layout, nodes not scattered randomly.
```

---

## §J. Administration & audit — màn 9.9 (optional)

```
[MASTER STYLE BLOCK], then:

Screen: ADMINISTRATION & AUDIT ("Quản trị" selected, admin-only). Center with tabbed sections: "Người dùng & phạm vi", "Chính sách runtime", "Nhật ký kiểm toán".
- Runtime policy card: an egress control row "Bộ định tuyến mô hình: Local (mặc định)" with a toggle "Cloud (chỉ khi bật)" and a pinned note "Dữ liệu nhạy (kế toán / lương / HR / PII) luôn xử lý cục bộ."
- Identity/scope: a table "Người dùng | Vai trò | Phòng ban | Trạng thái" with rows like "Nguyễn Văn A | Kế toán trưởng | Phòng KT | Hoạt động". Show role + department scope, NEVER tokens (any token rendered as "••••1234").
- Audit events timeline: rows "actor · action · scope · kết quả", e.g. "08:20 · Nguyễn Văn A · Duyệt bản nháp · TK 413 · Thành công", and one FAILED SAFETY CHECK row in warning surface: "08:31 · Hệ thống · Chặn egress · nội dung có nhãn PII · Đã chặn".
- System health mini row: "Trạng thái: Bình thường". No secrets, no connection strings, no API keys anywhere.
```

---

## Ghi chú vận hành khi sinh ảnh

- **Text tiếng Việt hay bị model bóp méo.** Nếu ảnh ra sai chữ: (1) giảm số nhãn trong một ảnh, (2) tăng độ phân giải, (3) sinh lại 2–3 lần rồi ghép, hoặc (4) coi ảnh là *layout reference* rồi chèn text thật bằng Figma/Canva sau.
- **Giữ nhất quán:** luôn dán lại §0 để màu/sidebar/scope-bar đồng bộ giữa các màn.
- **Kiểm tra tuân thủ mỗi ảnh:** có scope bar? mọi số có nhãn nguồn? trạng thái có label+icon (không chỉ màu)? có nhãn "bản nháp"? KHÔNG có %/donut/robot/gradient tím? Không lộ mục ngoài quyền? Nếu thiếu → sinh lại.
- **An toàn dữ liệu:** giữ tag "DỮ LIỆU MẪU", số tròn, tên giả — đây là ảnh có thể bị chiếu cho người ngoài.
```
