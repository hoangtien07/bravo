# SUMMARY — Tổng hợp Deep Research (5 track)

> Tổng hợp chéo 5 báo cáo deep research (A–E), chạy 2026-06-08, kiểm chứng đối kháng 3 phiếu. Mục tiêu: cải thiện dự án, tránh lỗi triển khai, tìm điểm mạnh, định vị BRAVO AI trên thị trường VN.
> Báo cáo gốc: [A](A-competitive-landscape.md) · [B](B-academic-technical.md) · [C](C-deployment-pitfalls.md) · [D](D-vietnam-market-positioning.md) · [E](E-vietnam-legal.md) · [F — re-verify rate-limit](F-reverification.md) · [G — ~17 đối thủ](G-competitor-deep-dive.md) · [H — tầng số liệu (semantic/calc/table-RAG)](H-data-layer-techniques.md) · [I — model tiếng Việt](I-vietnamese-models.md) · [J — RAG/agent/eval](J-rag-agent-eval.md).

## 1. Năm kết luận lớn (đã kiểm chứng)

1. **White space của BRAVO là THẬT và đã được xác nhận.** Cả Oracle/Microsoft/SAP (ERP-AI) lẫn MISA (đối thủ VN) đều **cloud-only** và đều **không** có on-prem sovereignty + RLS tầng dữ liệu + trích dẫn nguồn kế toán. MISA AVA làm phân tích tài chính NL nhưng không công bố gì về 3 thứ đó. *(A, D)*

2. **Số liệu sai là rủi ro #1 — và LLM nhỏ KHÔNG đáng tin để tính số.** FAITH: tính đa biến khiến nhiều model (kể cả 70B) về ~0%; Qwen-3-8B chỉ 30.6%. FailSafeQA: o3-mini bịa số 41% dưới nhiễu. → **Phải tính số ở tầng SQL deterministic; LLM chỉ diễn giải + trích dẫn.** *(B, C)*

3. **Lý do chọn on-prem là CHỦ QUYỀN, không phải chi phí.** Break-even on-prem vs cloud giá rẻ có thể 5–9 năm. Đừng bán bằng "tiết kiệm". *(C)*

4. **Đòn bẩy pháp lý CÓ THẬT nhưng HẸP (đã re-verify từ văn bản gốc).** Lưu dữ liệu cá nhân công dân VN trên cloud nước ngoài = chuyển dữ liệu xuyên biên giới → nghĩa vụ CTIA (hồ sơ + A05 trong 60 ngày; phạt tới 3 tỷ/5% DT). On-prem né lớp này. **NHƯNG đính chính quan trọng:** Khoản 6 Điều 20 Luật 91/2025 **MIỄN** cho dữ liệu cá nhân của **chính nhân viên** trên cloud → đòn bẩy **chỉ áp dụng cho dữ liệu KHÁCH HÀNG/nghiệp vụ, KHÔNG dùng cho HR/lương**. DPIA vẫn áp dụng cho mọi người (kể cả on-prem). *(E, F)*

5. **Thị trường lớn nhưng "đói giá trị".** ~80% DN VN dùng AI nhưng ít nơi thấy giá trị thực; ~50% pilot GenAI bỏ sau PoC (Gartner); chỉ 25% đưa ≥40% pilot lên production. → **đừng hứa doanh thu; mỗi tính năng gắn metric giá trị đo được.** *(C, D)*

## 2. Tác động tới thiết kế (cập nhật dự án)

| # | Phát hiện | Thay đổi đề xuất | Tài liệu | Trạng thái |
|---|-----------|------------------|----------|-----------|
| 1 | LLM nhỏ bịa số khi tính toán (B,C) | **LLM cấm tính số; tầng SQL deterministic tính, LLM diễn giải+cite** | ADR-0004, VISION §2/§4.1, ARCHITECTURE, SECURITY | ✅ áp dụng |
| 2 | Text-to-SQL sụp đổ trên ERP thật 21% (C) | **Không sinh SQL tự do; semantic layer/view đã duyệt** | ADR-0005, ARCHITECTURE | ✅ áp dụng |
| 3 | RAG injection không khử được ở model (C) | **Tài liệu = không tin cậy; chống render link exfil; scoped retrieval** | SECURITY §, security-rls-auditor | ✅ áp dụng |
| 4 | On-prem bán bằng chủ quyền (C,E) | **Sửa thông điệp moat: sovereignty + pháp lý, không phải chi phí** | VISION §3.1, ADR-0006 | ✅ áp dụng |
| 5 | White space MISA (A,D) | **Định vị: on-prem + không bịa số + RLS** | VISION §3.1/§5, ADR-0006 | ✅ áp dụng |
| 6 | Cần đo faithfulness/refusal (B) | **Bộ eval RAGAS+Trust-Score+benchmark masked-span tiếng Việt; cổng ra GĐ0** | ROADMAP, VISION §5.1 | ✅ áp dụng |
| 7 | Qwen nhỏ rủi ro số liệu (B) | **Cân nhắc lại kích thước Qwen / cloud opt-in cho suy luận** | ADR backlog | 🔶 chờ eval |
| 8 | Khoảng cách áp dụng→giá trị (C,D) | **Mỗi tính năng gắn metric; tránh "AI cho có"** | VISION §5, ROADMAP | ✅ áp dụng |

## 3. Cập nhật bản đồ cạnh tranh (đã kiểm chứng)

| Đối thủ | Triển khai | On-prem/LLM cục bộ | RLS tầng dữ liệu | Trích dẫn nguồn | Tiếng Việt/ERP VN |
|---------|-----------|--------------------|--------------------|-----------------|-------------------|
| Oracle NetSuite Next | Cloud (OCI) | ❌ | role-based | ✅ | ❌ |
| M365 Copilot Finance | Cloud (M365) | ❌ | ⚠️ kế thừa quyền lỏng | ✅ | ❌ |
| SAP Joule | Cloud (BTP) | ❌ | ✅ | ✅ | ❌ |
| Onyx (OSS) | **On-prem/air-gap** | ✅ | ⚠️ chưa rõ | — | ❌ |
| **MISA AVA** | **Cloud (Viettel IDC)** | ❌ | ❌ (không công bố) | ❌ (không công bố) | ✅ |
| **BRAVO AI (mục tiêu)** | **On-prem + hybrid** | ✅ | ✅ SQL RLS | ✅ tới ô/chứng từ | ✅ |

→ **Không đối thủ nào phủ đủ cả hàng cuối.** Đó là định vị của BRAVO.

**Khảo sát đầy đủ ~17 đối thủ** ([G](G-competitor-deep-dive.md)) khẳng định lại white space. **Xếp hạng đe doạ:** 🔴 MISA (cao — trùng chức năng, cloud-only) › 🟠 Glean / FPT / Base.vn (TB) › 🟡 Writer (self-host LLM + PalmyraFin). Không nền tảng nào (VN hay global) xác minh được đủ tổ hợp *on-prem/air-gapped + RLS-SQL + trích dẫn số + tiếng Việt/ERP-native*. Rủi ro chính là **tốc độ đối thủ**, không phải sản phẩm hiện hữu. 🆕 **Thông tư 99/2025 thay TT 200 từ 1/1/2026** — vừa là tuân thủ vừa là điểm bán (AI hiểu hệ thống tài khoản mới mà đối thủ ngoại không có).

## 4. Mười hành động ưu tiên (tác động × khả thi)

**Kiến trúc/kỹ thuật:**
1. **ADR: LLM không tính số** → tầng tính toán deterministic. *(ADR-0004)*
2. **ADR: Không sinh SQL tự do** → semantic layer/view kế toán đã duyệt. *(ADR-0005)*
3. **Phòng thủ prompt-injection** trong ingest (tài liệu không tin cậy + chống exfil). *(SECURITY)*
4. **Bộ eval tiếng Việt** (faithfulness/citation/refusal) làm cổng ra. *(ROADMAP GĐ0)*
5. **Pipeline bóc bảng hạng nhất** + retrieval schema+cell. *(skill rag-ingest-design)*

**Định vị/thị trường:**
6. **ADR định vị:** "AI tài chính có chủ quyền & không bịa số" (I+II). *(ADR-0006)*
7. **Đánh vào white space MISA** (on-prem + trích dẫn + RLS). *(VISION)*
8. **Sửa thông điệp on-prem** = chủ quyền/pháp lý, không phải chi phí. *(VISION)*

**Nghiên cứu/xác minh còn thiếu:**
9. **Nhờ pháp chế BRAVO xác nhận** miễn trừ dữ-liệu-nhân-viên + số điều mới (Luật 91/2025). *(E §1)*
10. **Khảo sát hành vi mua + mức sẵn-lòng-trả VN** (chưa có dữ liệu). *(D, E)*

## 5. Cảnh báo trung thực (rate-limit & độ tin cậy)

- **Rate-limit làm méo nhiều kết quả — ĐÃ KHẮC PHỤC:** các claim bị "giết oan" do rate-limit (phiếu trắng, không phải sai) đã được **re-verify từ nguồn gốc trong [F](F-reverification.md)** (pháp lý, Daloopa, Supabase RLS-on-vector, Onyx, Glean, Sage, thị trường VN, MISA). Còn lại chỉ là các claim bị **bác thật** (giá MISA cụ thể, "on-prem rẻ", "TableRAG SOTA").
- **Độ phủ một phần:** nhiều đối thủ bắt buộc (Glean, Dust, Hebbia, Zoho...) chưa được kiểm chứng sâu; chỉ 4 đối thủ chính + MISA.
- **Benchmark tiếng Anh:** mọi benchmark học thuật dùng tài liệu tài chính tiếng Anh/US-GAAP → chỉ là chỉ báo, BRAVO phải tự xây benchmark tiếng Việt/VAS.
- **Pháp lý (đã re-verify, [F](F-reverification.md)):** đòn bẩy có thật nhưng **hẹp** — chỉ dữ liệu khách hàng/nghiệp vụ (HR/lương được miễn). Trích theo khung 2025-2026; số điều mẫu NĐ 356/2025 cần luật sư.
- **Hành vi mua + định giá VN:** chưa có dữ liệu kiểm chứng — cần khảo sát sơ cấp.

## 6. Câu hỏi mở chuyển cho BRAVO (ngoài kỹ thuật)
1. Pháp chế xác nhận: miễn trừ dữ-liệu-nhân-viên-cloud (Luật 91/2025/NĐ 356/2025) có không? Số điều/mẫu DPIA+TIA mới?
2. Ai mua AI/ERP ở DN VN, ngân sách, điều gì thuyết phục?
3. BRAVO ERP đã có REST API read-only + hàng đợi draft chưa? (câu hỏi mở từ VISION §8 — vẫn cần)
4. Phần cứng khách điển hình (GPU?) để chốt kích thước Qwen.
