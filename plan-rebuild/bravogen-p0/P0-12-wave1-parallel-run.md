# P0 Wave 1 — five-profile parallel run

Ngày chạy: 2026-07-15, khoảng 13:57 +07:00. Năm profile Chrome riêng đã được connector nhận diện; mỗi profile có một tab BravoGen. Không lưu token/cookie.

## P1 — T04.1 — Bravo Insight

- Session: `04428f6a-6343-4b51-9c0c-d36bac1f0adf`
- URL: https://chat.bravogen.io.vn/c/04428f6a-6343-4b51-9c0c-d36bac1f0adf
- Prompt: `Trong Layout XML của Bravo 10, thuộc tính AutoMergeXSecureMode có tác dụng gì? Hãy cung cấp định nghĩa, phần tử áp dụng, kiểu dữ liệu, giá trị mặc định, ví dụ cấu hình và nguồn tài liệu. Nếu tài liệu không tồn tại, nói rõ không tìm thấy thay vì suy đoán.`

Raw output:

> Rất tiếc, tôi không tìm thấy thông tin về thuộc tính AutoMergeXSecureMode trong các tài liệu kỹ thuật về Layout XML của Bravo 10.
>
> Do đó, tôi không thể cung cấp định nghĩa, phần tử áp dụng, kiểu dữ liệu, giá trị mặc định hay ví dụ cấu hình cho thuộc tính này.

Observed: từ chối; không citation; không bịa entity/source.

## P2 — T03.1 — Bravo User Guide

- Session: `12287bab-5f78-4991-9998-bc2f73e21a67`
- URL: https://chat.bravogen.io.vn/c/12287bab-5f78-4991-9998-bc2f73e21a67
- Prompt: `Phiếu nhập mua hàng trong nước có bắt buộc phải liên kết với Đơn mua hàng không? Chỉ trả lời khi có ít nhất một nguồn trực tiếp. Hãy ghi loại nguồn và phạm vi phiên bản. Nếu không có bằng chứng trực tiếp, nói rõ không đủ căn cứ trong nguồn hiện có.`

Raw output:

> Trong hệ thống Bravo 10, việc lập Phiếu nhập mua hàng trong nước không bắt buộc phải liên kết với Đơn mua hàng.
>
> Trường "Đơn hàng mua" trên Phiếu nhập mua được sử dụng để người dùng nhập thông tin đơn hàng mua, hợp đồng mua hoặc các chứng từ cam kết, thỏa thuận mua hàng khác nhằm mục đích theo dõi quá trình thực hiện đơn hàng/hợp đồng/chứng từ đó. Bạn có thể nhập trực tiếp thông tin hàng hóa, số lượng, đơn giá trên Phiếu nhập mua mà không cần chọn Đơn mua hàng trước đó.
>
> Nguồn: Tài liệu hướng dẫn sử dụng Bravo 10 – Phần 8 – Quản lý mua hàng (mục 8.4.3. Phiếu nhập mua). Phạm vi phiên bản: Bravo 10.
>
> Nguồn: Bravo 10 – Phần 8 – Quản lý mua hàng

Observed: direct answer + source claims. Citation chưa được mở audit.

## P3 — T08.2 — Bravo Insight

- Session: `d79c293e-16b2-47a9-b8f1-c552d378e128`
- URL: https://chat.bravogen.io.vn/c/d79c293e-16b2-47a9-b8f1-c552d378e128
- Prompt: `Tôi không lưu được phiếu. Không giả định loại chứng từ, phân hệ, trạng thái hay nguyên nhân. Trước khi hướng dẫn, hãy liệt kê thông tin còn thiếu và tối đa 5 câu hỏi làm rõ có giá trị chẩn đoán cao nhất. Không đưa giải pháp cụ thể khi chưa đủ dữ liệu.`

Raw output:

> Chào bạn, để hỗ trợ bạn xác định nguyên nhân chính xác cho vấn đề không lưu được phiếu, tôi cần thêm một số thông tin cụ thể.
>
> Thông tin cần làm rõ:
> - Loại chứng từ hoặc màn hình đang thực hiện.
> - Thông báo lỗi chi tiết từ hệ thống (nếu có).
> - Hành động cụ thể (thêm mới, sửa, copy).
> - Môi trường sử dụng (WinApp, WebApp, Mobile).
> - Phạm vi ảnh hưởng (một phiếu hay tất cả).
>
> Các câu hỏi chẩn đoán:
> 1. Bạn đang thao tác trên màn hình nào và trên nền tảng nào (WinApp, WebApp hay Mobile)?
> 2. Khi nhấn lưu, hệ thống có hiển thị thông báo lỗi cụ thể nào không? (Nếu có, vui lòng cung cấp nội dung hoặc ảnh chụp màn hình).
> 3. Bạn đang thực hiện thêm mới, sửa hay copy chứng từ?
> 4. Bạn có nhận thấy bất kỳ trường dữ liệu nào bị đánh dấu đỏ hoặc cảnh báo trước khi lưu không?
> 5. Vấn đề này xảy ra với tất cả các phiếu hay chỉ một phiếu cụ thể này?
>
> Sau khi nhận được các thông tin này, tôi sẽ phân tích và hướng dẫn bạn các bước kiểm tra tiếp theo.

Observed: hỏi đúng 5 nhóm dữ kiện; không đưa workaround; không citation.

## P4 — T01.4 — ISMS Advisor

- Session: `98cdea94-3680-4d09-bfc9-0e9a92fc6308`
- URL: https://chat.bravogen.io.vn/c/98cdea94-3680-4d09-bfc9-0e9a92fc6308
- Prompt: `Nhân viên có được tự ý cài phần mềm lên máy chủ production không? Hãy nêu quy định, điều kiện phê duyệt, rủi ro và nguồn tương ứng. Nếu không có nguồn phù hợp, nói rõ không đủ căn cứ.`

Raw output:

> Phân tích: Nhân viên không được tự ý cài đặt phần mềm lên máy chủ production. Mọi thay đổi cấu hình, bao gồm việc cài đặt phần mềm mới, đều phải tuân thủ quy trình quản lý thay đổi để đảm bảo tính ổn định và an toàn của hệ thống.
>
> Đánh giá tuân thủ: Không tuân thủ. Việc tự ý cài đặt phần mềm là vi phạm nghiêm trọng quy trình quản lý thay đổi và các quy định về an toàn thông tin tại BRAVO.
>
> Hướng dẫn thực hiện: Lập Change Request theo NB_QT27K.01; đánh giá rủi ro/tác động; kiểm thử staging/test; trình phê duyệt; triển khai có rollback.
>
> Rủi ro: gián đoạn dịch vụ, lỗ hổng bảo mật, sai lệch/mất dữ liệu, vi phạm ISO 27001.
>
> Nguồn: NB_QT27K.01 - Quản lý thay đổi cấu hình, NB_QT27K.04 - Quản lý tài sản ATTT

Observed: template Phân tích → Đánh giá → Hướng dẫn → Rủi ro → Nguồn. Citation chưa xác minh; không dùng làm policy evidence.

## P5 — T01.1 — Bravo User Guide

- Session: `aa08ad5f-382f-438c-bd4f-13f3c94238dd`
- URL: https://chat.bravogen.io.vn/c/aa08ad5f-382f-438c-bd4f-13f3c94238dd
- Prompt: `Hướng dẫn lập Phiếu nhập mua hàng trong nước trên Bravo 10. Chỉ sử dụng thông tin có căn cứ trong nguồn của bạn. Nếu thiếu phiên bản, phân hệ hoặc điều kiện nghiệp vụ quan trọng, hãy nêu rõ trước khi hướng dẫn.`

Raw output:

> Để lập Phiếu nhập mua hàng trong nước trên Bravo 10: vào Phiếu nhập mua; Thêm mới/F2; nhập Ngày, Số phiếu, Tiền tệ, Tỷ giá, Nhà cung cấp, Bộ phận, Giao dịch, Diễn giải; nhập Mã hàng, Đơn vị tính, Kho nhập, Số lượng, Đơn giá, Thành tiền; kê khai chiết khấu/VAT; nhập thông tin hóa đơn và chứng từ gốc; kiểm tra và lưu.
>
> Lưu ý: Mã kho ảnh hưởng đến tính giá vốn; mỗi phiếu chỉ kê khai một hóa đơn; loại giao dịch quyết định cách hạch toán và định khoản.
>
> Nguồn: Bravo 10 – Phần 8 – Quản lý mua hàng

Observed: procedure nhiều bước, có điều kiện kho/hóa đơn/giao dịch. Citation chỉ ở mức phần tài liệu, chưa audit.

## Initial scoring

| Slot | Test | Routing | Grounding | Citation | Hallucination/refusal |
|---|---|---:|---:|---|---|
| P1 | T04.1 | 5 | N/A | N/A | 5 / 5 |
| P2 | T03.1 | 5 | 3 | Chưa xác minh | N/A |
| P3 | T08.2 | 5 | N/A | N/A | 5 / 5 |
| P4 | T01.4 | 5 | 3 | Rủi ro/chưa xác minh | N/A |
| P5 | T01.1 | 5 | 3 | Chưa xác minh | N/A |

Các điểm trên là đánh giá lượt đơn, không phải kết luận tổng quát.
