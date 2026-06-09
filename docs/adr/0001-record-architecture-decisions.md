# 0001. Dùng ADR để ghi quyết định kiến trúc

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** skill `/adr-new`, [README index](README.md)

## Bối cảnh (Context)
Dự án sẽ đưa ra nhiều quyết định kiến trúc có hệ quả lâu dài (vector store, model LLM cục bộ, cơ chế RLS, cách tích hợp ERP). Nếu không ghi lại *lý do* tại thời điểm quyết, sau này không ai nhớ vì sao chọn thế — dẫn tới tranh luận lặp lại và đảo ngược quyết định mù quáng. Dự án còn có 4 nguyên tắc bất biến cần được viện dẫn nhất quán trong mọi quyết định.

## Các phương án đã cân nhắc (Options)
1. **Không ghi chính thức** — dựa vào trí nhớ/chat. Nhược: mất ngữ cảnh, lặp tranh luận.
2. **Gom hết vào một tài liệu kiến trúc** — Nhược: không truy được lịch sử *vì sao đổi*, khó review từng quyết định.
3. **ADR — mỗi quyết định một file bất biến, có đánh số** — chuẩn ngành (Michael Nygard). Truy vết được, review được, không sửa quá khứ.

## Quyết định (Decision)
Dùng **ADR**. Mỗi quyết định kiến trúc lớn → một file `docs/adr/NNNN-*.md` theo mẫu trong `/adr-new`. ADR `Accepted` là bất biến; thay đổi = ADR mới `Supersedes`/`Superseded by`. Khuyến khích chạy `/council-review` trước khi viết ADR cho quyết định lớn.

## Hệ quả (Consequences)
- Tích cực: lịch sử quyết định minh bạch; onboard nhanh; tránh đảo ngược mù quáng; viện dẫn 4 nguyên tắc bất biến nhất quán.
- Tiêu cực: cần kỷ luật viết ADR (giảm thiểu bằng skill `/adr-new`).
- Ảnh hưởng 4 nguyên tắc bất biến: trung lập (cơ chế quản trị, không phải kỹ thuật sản phẩm).
- Việc tiếp: mỗi mục backlog trong [README](README.md) sẽ thành ADR khi chốt.

## Tham chiếu
Pattern ADR của Michael Nygard. Thực hành tương tự thấy trong tài liệu của arkon (`docs/`).
