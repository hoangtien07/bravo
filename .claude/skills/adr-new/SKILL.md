---
name: adr-new
description: "Tạo một Architecture Decision Record (ADR) mới trong docs/adr/ để ghi lại một quyết định kiến trúc quan trọng cùng bối cảnh, phương án và hệ quả. Triggers: adr, tạo adr, ghi quyết định kiến trúc, architecture decision, chốt quyết định, record decision."
allowed-tools: Read, Write, Glob
---

# adr-new: Tạo Architecture Decision Record

Mục tiêu: ghi lại một quyết định kiến trúc *ở thời điểm đưa ra*, kèm bối cảnh và lý do, để sau này không ai phải đoán "vì sao hồi đó chọn thế này".

## Khi nào dùng
Khi chốt một quyết định có hệ quả lâu dài: chọn vector store, mô hình LLM cục bộ, cơ chế RLS, cách tích hợp ERP, ranh giới module, v.v. Lý tưởng là chạy sau `/council-review`.

## Quy trình
1. **Xác định số thứ tự.** Liệt kê `docs/adr/` (Glob), lấy số lớn nhất + 1, định dạng 4 chữ số (`0007`).
2. **Đặt tiêu đề ngắn, mô tả quyết định** (vd: "Dùng pgvector thay vì FAISS cho vector store").
3. **Viết file** `docs/adr/NNNN-tieu-de-kebab.md` theo mẫu dưới.
4. **Cập nhật index** `docs/adr/README.md`: thêm một dòng trỏ tới ADR mới.
5. Nếu ADR thay thế một ADR cũ → đánh dấu ADR cũ là `Superseded by NNNN` và liên kết hai chiều.

## Mẫu ADR

```markdown
# NNNN. <Tiêu đề quyết định>

- **Trạng thái:** Proposed | Accepted | Superseded by [XXXX](XXXX-...md) | Deprecated
- **Ngày:** YYYY-MM-DD
- **Người quyết định:** <ai>
- **Liên quan:** <ADR/issue/tài liệu liên quan>

## Bối cảnh (Context)
Vấn đề là gì? Ràng buộc nào áp dụng (nhắc 4 nguyên tắc bất biến nếu liên quan: RLS, non-invasive, zero-hallucination, offline)? Vì sao phải quyết bây giờ?

## Các phương án đã cân nhắc (Options)
1. **Phương án A** — mô tả, ưu, nhược.
2. **Phương án B** — mô tả, ưu, nhược.
3. ...

## Quyết định (Decision)
Chọn phương án nào và **vì sao**. Nêu rõ đánh đổi đã chấp nhận.

## Hệ quả (Consequences)
- Tích cực: ...
- Tiêu cực / nợ kỹ thuật: ...
- Ảnh hưởng tới 4 nguyên tắc bất biến: ...
- Việc cần làm tiếp: ...

## Tham chiếu
- Phản hồi hội đồng (nếu có), repo tham chiếu, tài liệu.
```

## Nguyên tắc
- Một ADR = một quyết định. Đừng gộp nhiều quyết định.
- Ghi cả phương án bị loại và *lý do loại* — đó là phần giá trị nhất.
- ADR là bất biến sau khi `Accepted`: muốn đổi thì viết ADR mới thay thế, không sửa ADR cũ.
