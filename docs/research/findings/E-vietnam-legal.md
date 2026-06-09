# Findings E — Pháp lý VN & Chủ quyền dữ liệu (Deep Research bổ sung)

> Deep research, kiểm chứng 3 phiếu vs **văn bản pháp luật gốc** (chinhphu.vn, thuvienphapluat.vn) + EY/PwC/KPMG/DLA Piper. Chạy 2026-06-08. Run `wf_8ab4a06d-609`. **9/25 claim qua kiểm chứng** (nhiều claim luật bị rate-limit ở khâu verify — xem §3).

> 🔄 **CẬP NHẬT (đã re-verify):** các khoảng trống rate-limit của báo cáo này đã được xác minh lại từ văn bản gốc trong [findings/F](F-reverification.md). **Đính chính quan trọng:** miễn trừ dữ-liệu-nhân-viên-cloud (Khoản 6 Điều 20 Luật 91/2025) là **CÓ THẬT** → đòn bẩy on-prem chỉ áp dụng cho **dữ liệu khách hàng/nghiệp vụ**, không dùng cho HR/lương. Đọc F để có kết luận hoàn chỉnh.

## 0. Đòn bẩy pháp lý ĐÃ XÁC MINH cho định vị on-prem (dùng được, có điều kiện)

> **Lưu trữ/xử lý dữ liệu cá nhân của công dân VN (lương, HR, khách hàng) trên cloud đặt ở NƯỚC NGOÀI bị coi là "chuyển dữ liệu xuyên biên giới" → phát sinh thêm nghĩa vụ tuân thủ. Giải pháp on-prem/trong nước NÉ được lớp nghĩa vụ này.**

Bằng chứng (3-0 vs nguồn gốc):
1. **Định nghĩa rộng:** chuyển dữ liệu ra nước ngoài gồm cả *"dùng địa điểm ngoài lãnh thổ để xử lý dữ liệu cá nhân công dân VN"* và *"hệ thống tự động nằm ngoài lãnh thổ"* (NĐ 13/2023 Điều 2.14) → **bao trùm dịch vụ cloud nước ngoài** (ITIF, DLA Piper, KPMG, EY đồng thuận).
2. **Hồ sơ đánh giá tác động chuyển dữ liệu (TIA):** nộp Bộ Công an (Cục An ninh mạng A05), Mẫu 06, **trong 60 ngày** (NĐ 13 Điều 25).
3. **Luật BVDLCN (Luật 91/2025/QH15):** thông qua 26/6/2025, **hiệu lực 1/1/2026** → **đang có hiệu lực** (luật cấp Luật đầu tiên, thay NĐ 13, kèm NĐ 356/2025). Khung DPIA + chuyển-xuyên-biên-giới **được kế thừa**; DPIA nay lập 1 lần/đời hoạt động, cập nhật mỗi 6 tháng.

→ **Lập luận bán hàng (đã có cơ sở):** *"BRAVO chạy on-prem, dữ liệu ở trong nước → không kích hoạt nghĩa vụ chuyển dữ liệu xuyên biên giới mà giải pháp cloud nước ngoài phải gánh."*

## 1. ⚠️ ĐIỀU KIỆN QUAN TRỌNG — không phóng đại

1. **NĐ 13/2023 đã HẾT hiệu lực từ 1/1/2026** (thay bằng Luật 91/2025 + NĐ 356/2025). Các số điều/mẫu (Điều 24/25, Mẫu 04/06) **đúng về lịch sử nhưng thuộc khung CŨ** — **phải trích lại theo Luật 91/2025 + NĐ 356/2025** trước khi đưa vào tài liệu bán hàng. (Số điều mới — Điều 20/21 — chưa xác minh được do rate-limit.)
2. **DPIA là nghĩa vụ PHỔ QUÁT** (mọi bên xử lý dữ liệu cá nhân, kể cả on-prem). → On-prem **giảm** gánh nặng (né TIA xuyên biên giới) **nhưng KHÔNG xoá** DPIA cơ bản. Đừng nói "on-prem là không phải tuân thủ gì".
3. **🚨 ĐIỂM PHẢI HỎI LUẬT SƯ (quyết định độ mạnh của lập luận):** có nguồn (EY) cho rằng Luật 2025/NĐ 356/2025 **THÊM miễn trừ** cho tổ chức lưu dữ liệu **nhân viên của chính mình** trên cloud → nếu đúng, **làm yếu** lập luận "cloud = gánh nặng tuân thủ cho HR/lương". Claim này **chưa xác minh** (1-0). **BRAVO phải nhờ pháp chế xác nhận** trước khi dùng làm điểm bán chính.
4. **Nội địa hoá dữ liệu** (NĐ 53/2022, Luật Dữ liệu 60/2024): mọi claim **chưa xác minh** (rate-limit) → góc "bắt buộc lưu trong nước" **chưa có cơ sở**, cần nghiên cứu lại.

## 2. Khoảng trống chưa trả lời
- **Hành vi mua B2B VN** (ai quyết định, chu kỳ, ngân sách, điều gì thuyết phục): **không claim nào qua kiểm chứng** → cần khảo sát sơ cấp riêng.
- Quy định kế toán/hoá đơn điện tử (Thông tư 200, NĐ hoá đơn) về lưu trữ/toàn vẹn dữ liệu: chưa có claim sống sót.
- Số điều/mẫu chính xác của khung mới (Luật 91/2025 + NĐ 356/2025).

## 3. Ghi chú phương pháp
Rất nhiều agent kiểm chứng bị **rate-limit** (phiếu trắng) → nhiều claim luật đúng nhưng bị "giết" oan (vd NĐ 53/2022 ngày ban hành, Luật Dữ liệu 60/2024). Các claim **đã xác minh 3-0** ở §0 là vững (đối chiếu trực tiếp văn bản gốc). Các claim ở "refuted" phần lớn là **chưa xác minh** chứ không phải sai.

## 4. Hành động cho BRAVO (rút từ Track E)
1. **[PHÁP CHẾ] Nhờ luật sư BRAVO xác nhận 2 điểm quyết định:** (a) miễn trừ dữ liệu-nhân-viên-trên-cloud có tồn tại trong Luật 91/2025/NĐ 356/2025 không; (b) số điều/mẫu mới cho DPIA + TIA. *(Quyết định độ mạnh của moat pháp lý.)*
2. **[ĐỊNH VỊ] Dùng lập luận pháp lý ở mức đã xác minh:** "on-prem → dữ liệu trong nước → né nghĩa vụ chuyển xuyên biên giới" — **không** nói "on-prem miễn mọi tuân thủ".
3. **[TÀI LIỆU] Trích theo khung mới** (Luật 91/2025 + NĐ 356/2025), không trích NĐ 13 như luật hiện hành.
4. **[KHẢO SÁT] Hành vi mua + quy định kế toán** — gap còn lại.

## 5. Nguồn chính đã xác minh
- NĐ 13/2023 toàn văn: xaydungchinhsach.chinhphu.vn, thuvienphapluat.vn (465185).
- Luật 91/2025/QH15: thuvienphapluat.vn (625628), chinhphu.vn (docid 214590), EY Vietnam Legal Alert 7/2025, PwC Legal.
- NĐ 356/2025 (điểm mới): luatvietnam.vn (106269).
- Bình luận: DLA Piper, KPMG VN, Tilleke & Gibbins, ITIF (9/6/2025), Freshfields.

---
*Phương pháp: 5 góc → 24 nguồn → 101 claim → kiểm chứng 25 → 9 xác nhận / 16 bị giết (đa số do rate-limit) → 7 sau tổng hợp.*
