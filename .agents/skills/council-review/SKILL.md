---
name: council-review
description: "Triệu tập Hội đồng cố vấn BRAVO AI Copilot để thẩm định một thiết kế, quyết định kiến trúc, hoặc tính năng từ 5 góc độ độc lập (an ninh/RLS, nghiệp vụ kế toán, RAG, triển khai on-prem, chiến lược sản phẩm) rồi tổng hợp thành phán quyết. Triggers: council review, hội đồng, thẩm định thiết kế, review quyết định, đánh giá đa chiều, convene council, hỏi hội đồng."
---

# council-review: Triệu tập Hội đồng cố vấn

Mục tiêu: thẩm định một đề xuất từ nhiều góc độ chuyên môn **độc lập** trước khi chốt, để bắt lỗi mà một góc nhìn đơn lẻ bỏ sót — đặc biệt các lỗi chí mạng của dự án này (rò phân quyền, sai số liệu kế toán, ảo tưởng RAG, phụ thuộc cloud, lãng phí công sức).

## Khi nào dùng
- Trước khi chốt một quyết định kiến trúc lớn (sẽ thành ADR).
- Khi thiết kế một tính năng chạm tới dữ liệu nhạy cảm, số liệu tài chính, hoặc tích hợp ERP.
- Khi cần phản biện đa chiều một phương án.

## Hội đồng (5 thành viên — định nghĩa ở `.Codex/agents/`)
| Agent | Lăng kính |
|-------|-----------|
| `security-rls-auditor` | An ninh, RLS, quyền riêng tư, tuân thủ PDPD |
| `erp-accounting-expert` | Tính đúng số liệu, nghiệp vụ kế toán VN |
| `rag-architect` | Ingestion, trích dẫn, chống ảo tưởng |
| `onprem-deployment-engineer` | Sàn offline + hybrid, Docker/K8s, LLM cục bộ |
| `product-strategist` | Giá trị, ưu tiên MVP, mô hình bán |

## Quy trình

1. **Đóng khung đề xuất.** Tóm tắt rõ ràng *cái đang được thẩm định* thành 3–6 câu: vấn đề, phương án đề xuất, các ràng buộc liên quan. Nếu mơ hồ, làm rõ với người dùng trước.

2. **Chọn thành viên liên quan.** Mặc định triệu tập cả 5. Có thể bỏ thành viên rõ ràng không liên quan (vd thuần UI thì có thể bỏ erp-accounting-expert) — nhưng **luôn giữ `security-rls-auditor`** cho bất cứ thứ gì chạm dữ liệu.

3. **Gửi song song.** Dùng Task tool gọi các subagent **trong một message duy nhất** (chạy đồng thời). Gửi cho mỗi thành viên cùng một bản đóng khung đề xuất + đường dẫn tài liệu liên quan (`docs/...`, repo tham chiếu). Yêu cầu mỗi thành viên trả về: **phán quyết** + danh sách phát hiện theo mức độ + khắc phục cụ thể.

4. **Tổng hợp.** Sau khi cả hội đồng phản hồi, trình bày:
   - **Bảng phán quyết** (mỗi thành viên: ✅/⚠️/❌ + một câu).
   - **Vấn đề chặn (blocking)** — bất kỳ ❌ nào, đặc biệt từ security hoặc accounting, là chặn.
   - **Điểm đồng thuận** và **điểm xung đột** giữa các thành viên (vd: strategist muốn nhanh, security muốn chặt — nêu rõ đánh đổi).
   - **Khuyến nghị tổng hợp**: GO / GO-WITH-CHANGES / NO-GO + các thay đổi bắt buộc.
   - Nếu đủ lớn để thành quyết định kiến trúc → gợi ý chạy `/adr-new`.

## Nguyên tắc
- Phán quyết ❌ từ `security-rls-auditor` hoặc `erp-accounting-expert` về một rủi ro Critical là **quyền phủ quyết** — không "GO" cho tới khi giải quyết.
- Không tự làm dịu phản hồi của hội đồng. Trình bày trung thực cả bất đồng.
- Tổng hợp phải *ra quyết định được*, không chỉ liệt kê ý kiến.
