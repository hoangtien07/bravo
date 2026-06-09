# Findings F — Re-verify các khoảng trống do rate-limit (vòng bổ sung)

> Mục đích: xác minh lại các claim bị **rate-limit giết oan** (abstain ≠ sai) ở track A/D/E, dùng 3 agent gọn đọc **nguồn gốc** (không full-workflow → không dính cascade). Chạy 2026-06-08. Tất cả có dẫn chứng nguồn gốc.

## 🔴 0. ĐÍNH CHÍNH QUAN TRỌNG — Đòn bẩy pháp lý hẹp hơn ta tưởng

**Luật BVDLCN 91/2025 — Khoản 6 Điều 20: MIỄN đánh giá tác động chuyển dữ liệu xuyên biên giới cho tổ chức lưu dữ liệu cá nhân của CHÍNH NHÂN VIÊN mình trên cloud.** (Xác minh CAO, trích trực tiếp toàn văn luật thuvienphapluat.vn + EY-Vietnam.)

→ **Hệ quả:** lập luận *"cloud = gánh nặng tuân thủ cho dữ liệu HR/lương"* **SAI một phần — KHÔNG được dùng làm điểm bán on-prem.** Doanh nghiệp lưu dữ liệu nhân viên *của chính mình* trên cloud (kể cả cloud nước ngoài) được **miễn** lập hồ sơ CTIA.

**Nhưng đòn bẩy vẫn còn — cho dữ liệu KHÁC:**
- ✅ **Dữ liệu KHÁCH HÀNG / đối tác / nhân viên bên thứ ba** trên cloud nước ngoài **VẪN** = chuyển dữ liệu xuyên biên giới → **CTIA** (hồ sơ nộp Cục An ninh mạng A05 trong 60 ngày; phạt tới **3 tỷ đồng / 5% doanh thu năm trước**; A05 báo <20% hồ sơ đạt chuẩn). **On-prem né hoàn toàn lớp này.** (Khoản 1–2 Điều 20, xác minh CAO.)
- Định nghĩa "chuyển xuyên biên giới" rất rộng: gồm lưu trên server nước ngoài, cho tổ chức nước ngoài, *hoặc dùng nền tảng/cho truy cập-xử lý từ nước ngoài*.

→ **Thông điệp pháp lý ĐÚNG cho BRAVO:** *"On-prem giữ dữ liệu **khách hàng & nghiệp vụ** trong nước → tránh nghĩa vụ & rủi ro phạt khi chuyển dữ liệu xuyên biên giới."* **Không** quảng cáo cho dữ liệu HR nội bộ.

## 1. Khung pháp lý — số điều & văn bản (xác minh từ nguồn gốc)
- **Luật 91/2025/QH15** (hiệu lực 1/1/2026): **Điều 20** = chuyển dữ liệu xuyên biên giới (gồm CTIA); **Điều 21** = DPIA. Thay Điều 25/24 của NĐ 13/2023 cũ. (CAO)
- **NĐ 356/2025/NĐ-CP** (ban hành 31/12/2025, hiệu lực 1/1/2026, 42 điều, thay NĐ 13): biểu mẫu CTIA/DPIA — *số điều cụ thể cần luật sư đối chiếu bản công báo* (fetch cho Điều 18/19, có nguồn dẫn Điều 17 danh mục miễn trừ). (TRUNG BÌNH)
- **DPIA là nghĩa vụ PHỔ QUÁT** (mọi bên xử lý dữ liệu cá nhân, kể cả on-prem) → on-prem **giảm** (né CTIA) chứ **không xoá** tuân thủ. (CAO)
- **NĐ 53/2022** (ban hành 15/8/2022, hiệu lực 1/10/2022): nội địa hoá nhắm **dịch vụ mạng** (MXH, TMĐT, viễn thông); DN nước ngoài chỉ phải nội địa hoá khi có **quyết định của Bộ trưởng Bộ Công an**. **Không** phải đòn bẩy riêng cho on-prem (cloud-tại-VN cũng thoả). (CAO)
- **Luật Dữ liệu 60/2024** (thông qua 30/11/2024, hiệu lực 1/7/2025): dữ liệu *thông thường* được tự do chuyển; chỉ "dữ liệu cốt lõi/quan trọng" bị siết (phạm vi hẹp). **Không** tạo đòn bẩy on-prem cho dữ liệu nghiệp vụ thường. (CAO)
- **Kế toán/hoá đơn điện tử (NĐ 123/2020, đã sửa bởi NĐ 70/2025):** yêu cầu **toàn vẹn** (không sửa) + **lưu 10 năm** (Luật Kế toán 2015/NĐ 174/2016). **KHÔNG** có yêu cầu lưu trong nước. → "kế toán bắt buộc lưu trong nước" là **suy luận sai, không dùng**; nhưng *toàn vẹn + truy xuất 10 năm* là lợi thế vận hành on-prem hợp lệ. (CAO)

## 2. Kỹ thuật/cạnh tranh (track A casualties — đều XÁC NHẬN)
- **Daloopa benchmark (XÁC NHẬN, CAO):** LLM trần 11.2% (Gemini 2.5 Pro) → 63.8% (GPT-5 Thinking); **grounded (Claude Opus 4.1 + Daloopa MCP) = 94.2%** exact-match (n=500 số tài chính). → **Bằng chứng mạnh: grounding/truy hồi có cấu trúc đánh bại bịa số** — dùng được cho luận điểm zero-hallucination của BRAVO. (FinRetrieval, arXiv 2603.04403)
- **Supabase RLS-on-vector (XÁC NHẬN, CAO):** Postgres RLS lọc **cả vector similarity search** ở tầng SQL, không cần lọc tầng ứng dụng. Trích nguyên văn: *"semantic search over these sections... will continue to respect these RLS policies."* → **Tiền lệ kỹ thuật trực tiếp cho RLS-trên-pgvector của BRAVO.** (supabase.com/docs/guides/ai/rag-with-permissions)
- **Onyx (XÁC NHẬN, CAO):** self-host LLM (Ollama/vLLM/LiteLLM) + air-gapped ✅; **permission-aware ACL document-level nhưng CHỈ ở Enterprise Edition** (CE là MIT nhưng chỉ Public/Private + gán thủ công); mirror ACL từ connector (8 nguồn), **khác** mô hình RLS phòng ban của BRAVO. → *Khi so sánh, ghi rõ Onyx ACL-sync là EE-only, không phải RLS phòng ban.*
- **Glean on-prem (XÁC NHẬN, CAO):** công bố triển khai on-prem qua **Dell AI Factory 20/05/2025** (nhắm healthcare/financial services).
- **Sage Copilot rò chéo khách hàng (XÁC NHẬN, CAO; phạm vi TB):** The Register 20/01/2025 — Sage tạm ngưng Copilot sau khi nó kéo dữ liệu tài khoản khách khác khi liệt kê hoá đơn. *Sage giảm nhẹ "sự cố nhỏ, không lộ hoá đơn".* → Bằng chứng cho nhu cầu cô lập đa-tenant/RLS chặt; **trích kèm phản hồi của Sage** để không bị phản bác.

## 3. Thị trường VN (track D/E casualties)
- **Quy mô thị trường AI VN (XÁC MINH PHẦN LỚN, TB):** con số phân tán theo định nghĩa — **~750–932 triệu USD (2024–2025), CAGR ~15–28% tuỳ nguồn** (IMARC, Statista, BlueWeave). *Không có con số "chính thống" duy nhất → luôn ghi rõ hãng + phạm vi.* (Bỏ con số R&M 2023 "23 tỷ/2028" — lỗi thời, quá lạc quan.)
- **Rào cản chuyển đổi số (XÁC NHẬN, CAO — Cục PTDN/Bộ KH&ĐT 2021, 1.300 DN):** chi phí **60.1%** (cao nhất) · đổi thói quen 52.3% · thiếu nhân lực 52.3% · hạ tầng 45.4% · ... · **sợ rò rỉ dữ liệu 23.4% (THẤP NHẤT)**. ⚠️ *Lưu ý dịch chuyển theo thời gian:* lo ngại bảo mật đã tăng tới 2025 (Gartner 6/2025: 48% coi rủi ro bảo mật là top-3). **Đừng trộn 2 mốc thời gian.**
- **Hành vi mua (TB — phần lớn là B2B toàn cầu, suy luận cho VN):** CEO/chủ DN = người mua kinh tế (VN 97–98% SME, thường gộp vai trò, **ít khi có CIO riêng**); CFO quyền phủ quyết tài chính (~79% deal toàn cầu cần CFO duyệt); chu kỳ bán phần mềm DN ~11.5–12 tháng, 12–22 bên liên quan; ~41% người mua đã có nhà cung cấp ưa thích trước khi đánh giá → **tham chiếu khách hàng + hiện diện sớm rất quan trọng**. *Chưa có khảo sát định lượng riêng VN — cần khảo sát sơ cấp.*
- **MISA cloud-only (XÁC NHẬN, CAO — nguồn chính thức MISA):** amis.misa.vn ghi rõ "phần mềm kế toán **online**", không có tuỳ chọn on-prem cho dòng online; host **Viettel IDC** (xác nhận trên sme.misa.vn, Tier 3, ISO 27001, CSA Star, GDPR — *bài 2016, cấu hình 2026 có thể đổi*); AVA ra mắt 15/12/2023.
- **Ứng dụng AI (XÁC NHẬN, CAO — AWS×Strand 18/9/2025):** **18% DN VN** đã triển khai AI (tăng từ 13%), **74% còn ở mức cơ bản**; khoảng cách giá trị: Talentnet 10/2025 — 91% dùng AI nhưng **chỉ ~50% thấy hiệu quả thực**, chỉ 14% có quy định AI áp dụng hiệu quả. *(Tỉ lệ 18%/73%/91% đo quần thể khác nhau — dùng 18% AWS cho toàn nền kinh tế.)*

## 4. Tác động — cập nhật tài liệu dự án
| Phát hiện re-verify | Cập nhật |
|---------------------|----------|
| Miễn trừ dữ-liệu-nhân-viên-cloud (0) | Đính chính moat pháp lý: chỉ dùng cho dữ liệu **khách hàng/nghiệp vụ**, không dùng cho HR → VISION §3.1, SECURITY §6, [E §0](E-vietnam-legal.md) |
| Daloopa 94% grounded (2) | Bằng chứng cho ADR-0004 (zero-hallucination via grounding) |
| Supabase RLS-on-vector (2) | Tiền lệ kỹ thuật → ARCHITECTURE/SECURITY (RLS lọc vector ở SQL khả thi) |
| MISA cloud-only xác nhận (3) | Củng cố white space (A, D) |
| 18% adoption + value gap (3) | Củng cố "đói giá trị" → VISION §5 |

## 5. Vẫn cần BRAVO/luật sư (ngoài tầm web)
- Ranh giới chính xác miễn trừ Khoản 6 Điều 20 (có gồm lương/BHXH/đánh giá hiệu suất?); số điều mẫu NĐ 356/2025.
- Khảo sát **định lượng riêng VN** về người ra quyết định mua + mức sẵn-lòng-trả.
- Trạng thái data center MISA 2026 (nguồn xác nhận là bài 2016).
