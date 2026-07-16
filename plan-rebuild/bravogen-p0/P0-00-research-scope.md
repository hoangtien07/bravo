# P0-00 — BravoGen black-box research scope

## Mục tiêu

Khảo sát hành vi được phép của ba mode BravoGen để xác định năng lực sản phẩm, giới hạn và benchmark cần có cho BRAVO AI Copilot tương lai.

Modes:

- Bravo User Guide
- Bravo Insight
- ISMS Advisor

## Câu hỏi nghiên cứu

1. Ba mode khác nhau về phạm vi, nguồn, template và hành vi từ chối đến đâu?
2. Có dấu hiệu retrieval thật hay câu trả lời chủ yếu đến từ kiến thức nền?
3. Citation có tồn tại, truy cập được và hỗ trợ claim không?
4. “Knowledge Graph” có biểu hiện dữ liệu quan hệ ổn định hay chỉ là synthesis dạng graph?
5. Hệ thống phản ứng thế nào với thực thể giả, thiếu ngữ cảnh, phiên bản giả và mâu thuẫn?
6. Hệ thống duy trì/correct context, branch và follow-up như thế nào?
7. Mode boundary, permission behavior và prompt-in-document defense có đáng tin không?
8. Những hành vi nào lặp lại đủ ổn định để trở thành product requirement?

## Giới hạn

- Chỉ dùng chức năng người dùng bình thường được cấp quyền.
- Không lấy system prompt, API key, credential, dữ liệu người dùng khác hoặc bí mật thương mại.
- Không dò endpoint trái phép, bypass quyền, gây tải hoặc trích xuất hàng loạt corpus.
- Không gửi dữ liệu khách hàng.
- Không yêu cầu chain-of-thought; chỉ yêu cầu execution summary ở mức công khai và cho phép trả lời “Không thể xác nhận”.

## Quy tắc bằng chứng

- `OBSERVED`: trực tiếp thấy từ input/output, UI, citation hoặc hành vi lặp lại.
- `INFERRED`: giả thuyết giải thích nhiều quan sát, kèm phản chứng và confidence.
- `UNVERIFIED`: lời tự thuật hoặc tuyên bố chưa có test xác nhận.

Các tên như `search_user_guide`, `search_user_guide_graph`, namespace hay “epistemic validation” hiện chỉ là `UNVERIFIED`.

## Phương pháp

- Mỗi phép so sánh chỉ đổi một biến.
- Test quan trọng chạy tối thiểu 2 phiên độc lập; mục tiêu 3 lần/mode khi đủ quota.
- Lưu raw output đầy đủ trước khi phân tích.
- Không coi tự kiểm định của BravoGen là bằng chứng độc lập.
- Không đưa ra kiến trúc BRAVO trong P0.

## Điều kiện hoàn thành

Áp dụng exit criteria trong `../01-MASTER-EXECUTION-PLAN.md`. P0 kết thúc bằng ba danh sách: đã xác minh, có thể suy luận và vẫn chưa biết.
