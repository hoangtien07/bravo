# BRAVO-AI-GAP-USP-MAP — Khoảng trống và USP AI theo vòng đời phần mềm BRAVO

> Nguồn đã nạp: 19 mindmap BRAVO 10, `Tài liệu bravo 10 cho khối kỹ thuật.docx`, bộ KQPT/PTNV B10R1, `UserGuide_B10_Basic rules.pdf`, `BRAVO_BI_Guidelines_Full.pdf`.
> Mục tiêu: hiểu BRAVO như một hệ ERP và một quy trình làm phần mềm đầy đủ, rồi xác định chỗ AI có USP rõ ràng, đo được, không phá quy trình nghiệp vụ.

## 1. Nhận định nền

BRAVO không chỉ là phần mềm kế toán. Đây là ERP có ba lớp tài sản tích lũy:

1. **Nghiệp vụ chuẩn**: mua hàng, bán hàng, kho, kế toán, giá thành, HRM, QC, sản xuất, task, CRM, mobile.
2. **Nền kỹ thuật nội bộ**: hệ bảng `B00/B10/B20/B30`, chứng từ `B30AccDoc`, tài liệu kinh doanh `B30BizDoc`, layout, evaluator, stored procedure, view GetData, quy trình duyệt, log, khóa dữ liệu.
3. **Tri thức triển khai**: KQPT/PTNV, tài liệu khối kỹ thuật, user guide, mẫu in, dashboard, offline mobile, notification, file attached, IFRS/TT99, các bài toán khách hàng thường yêu cầu chỉnh.

USP AI phải dựa trên cả ba lớp này. Nếu chỉ là chatbot hỏi đáp tài liệu thì dễ bị generic AI bắt chước. Nếu hiểu được **nghiệp vụ + schema + vòng đời triển khai BRAVO** thì trở thành lợi thế riêng.

## 2. Vòng đời phần mềm BRAVO và khoảng trống AI

| Giai đoạn | Người dùng chính | Tài sản đầu vào | Khoảng trống hiện tại | AI nên hỗ trợ |
|---|---|---|---|---|
| BA/PTNV | BA, PTSP, tư vấn | KQPT, quy trình khách, user guide, luật/chuẩn mực | Tài liệu dài, nhiều bản, khó so sánh phạm vi, khó tái dùng phân tích cũ | tìm case tương tự, tóm tắt phạm vi, sinh acceptance criteria, checklist câu hỏi khảo sát |
| Thiết kế kỹ thuật | Dev, kiến trúc, PTSP | tài liệu khối kỹ thuật, schema B00/B10/B20/B30, layout/eval/procedure | Khó nhớ đúng bảng/trường/procedure; risk sửa sai tầng | gợi ý bảng/view/procedure liên quan, impact map, guardrail naming/DB convention |
| Dev chỉnh sửa theo yêu cầu | Dev, kỹ thuật triển khai | yêu cầu khách, KQPT, layout, report, mẫu in | Yêu cầu nghiệp vụ thường biến thành sửa layout/report/procedure lẻ tẻ; khó biết ảnh hưởng liên phân hệ | phân loại yêu cầu: config/layout/report/code; sinh plan kỹ thuật và test case |
| Kiểm thử | QA, BA, dev | KQPT, acceptance, quy trình nghiệp vụ | Testcase thủ công, dễ bỏ sót exception và phân quyền | sinh testcase theo role, dữ liệu, exception, RLS, khóa dữ liệu, duyệt |
| Triển khai | Kỹ thuật triển khai, tư vấn | master data, số dư đầu kỳ, tồn kho, branch, fiscal year, phân quyền | Sai mô hình đơn vị/kho/số dư đầu kỳ gây hậu quả lớn, sửa rất tốn | checklist triển khai, cảnh báo thiếu dữ liệu, reconciliation trước go-live |
| Đào tạo/hướng dẫn | Tư vấn, support, key user | user guide, mindmap, video/hình ảnh, quy trình | Người dùng khó tìm đúng chức năng, hỏi lặp lại nhiều | trợ lý hướng dẫn theo vai trò và quy trình, trả lời có trích dẫn |
| Hỗ trợ sau go-live | Helpdesk, kỹ thuật, khách hàng | ticket, log, lỗi, tài liệu kỹ thuật, user guide | Tốn thời gian tra cứu lỗi/cấu hình, tri thức nằm rải rác ở người lâu năm | tự phục vụ câu hỏi, gợi ý nguyên nhân, hướng xử lý, escalation packet |
| Năng suất người dùng cuối | Kế toán, kho, mua hàng, bán hàng, HR | chứng từ, báo cáo, dashboard, tài liệu đính kèm | Nhập liệu, đối chiếu, báo cáo, tìm chứng từ còn thủ công | copilot chứng từ, đối chiếu, giải thích báo cáo, tạo nháp chờ duyệt |

## 3. Context kỹ thuật BRAVO cần AI hiểu

Từ tài liệu khối kỹ thuật:

- **Hai database chính**: một database hệ thống và một database dữ liệu khách hàng.
- **Quy ước bảng**:
  - `B00`: bảng hệ thống.
  - `B10`: bảng khai báo công thức báo cáo.
  - `B20`: bảng danh mục.
  - `B30`: bảng chứng từ/phát sinh.
- **Quy ước object**:
  - View bắt đầu bằng `v...`.
  - Stored procedure theo `usp_*`.
  - Function theo `ufn_*`, function hệ thống theo `ufn_sys_*`.
- **Mô hình chứng từ**:
  - `B30AccDoc`: đầu phiếu kế toán.
  - `B30AccDocPurchaseHdr`, `B30AccDocSalesHdr`, `B30AccDocItemHdr`: đầu phiếu theo nhóm nghiệp vụ.
  - Các bảng chi tiết liên kết bằng `Stt`, bảng con/cháu bằng `RowId`.
  - `B30BizDoc`: tài liệu kinh doanh không định khoản như PO, hợp đồng, báo giá, khế ước.
- **Mẫu mua hàng chuẩn**:
  - `PR`: yêu cầu mua hàng - `B30BizDoc` + `B30BizDocDetail`.
  - `PQ`: đề nghị chào hàng - `B30BizDoc` + `B30BizDocDetail`.
  - `QR`: báo giá NCC - `B30BizDoc` + `B30BizDocDetail`.
  - `PO`: đơn đặt hàng mua - `B30BizDoc` + `B30BizDocDetailPO`.
  - `C1`: hợp đồng mua - `B30BizDoc` + `B30BizDocDetail` + lịch thanh toán.
  - `RC`: lệnh nhập hàng - `B30BizDoc` + `B30BizDocDetail`.
  - `NM`: phiếu nhập mua - `B30AccDoc` + `B30AccDocPurchase` + `B30AccDocAtchDoc` + `B30AccDocApplyPrepayment`.
  - `NK`: phiếu nhập khẩu - cùng nhóm purchase nhưng có thuế nhập khẩu/TTĐB/BVMT/VAT nhập khẩu.
  - `CP`: chi phí mua hàng - purchase expense, lấy dữ liệu từ phiếu nhập để phân bổ.
  - `XT`: xuất trả NCC - `B30AccDocPurchaseReturn` + FIFO + bù trừ công nợ hóa đơn nhập.

Hệ quả: mọi draft AI muốn "đúng BRAVO" phải biết nó đang đề xuất vào nhánh `BizDoc` hay `AccDoc`, chứng từ nào là nguồn kế thừa, bảng chi tiết nào chịu tác động, và báo cáo/view nào sẽ bị ảnh hưởng.

## 4. 8 USP AI nên theo đuổi

### USP-1: BRAVO Implementation Copilot

**Người dùng:** kỹ thuật triển khai, tư vấn, support.

**Nỗi đau:** phải nhớ quy trình cài đặt, license, log, backend, database, đơn vị cơ sở, tham số, phân quyền, khóa dữ liệu, số dư đầu kỳ.

**AI hỗ trợ:** hỏi đáp kỹ thuật có trích dẫn; checklist go-live; cảnh báo rủi ro khi mô hình branch/kho/số dư đầu kỳ chưa chốt; gợi ý tài liệu liên quan.

**Đo giá trị:** giảm giờ tra cứu/ticket; giảm lỗi go-live; giảm ngày bàn giao.

### USP-2: BRAVO BA/PTNV Copilot

**Người dùng:** BA, PTSP, tư vấn.

**Nỗi đau:** KQPT dài, mỗi bài toán có lịch sử sửa đổi, cơ sở phân tích, phạm vi, chức năng, giao diện, testcase; khó tái dùng phân tích cũ.

**AI hỗ trợ:** tìm yêu cầu tương tự, tóm tắt phạm vi, so sánh bản chuẩn với yêu cầu khách, sinh câu hỏi khảo sát, sinh acceptance criteria.

**Đo giá trị:** giảm thời gian viết KQPT; tăng tỷ lệ reuse; giảm số lần clarify giữa BA-dev-test.

### USP-3: Customization Impact Copilot

**Người dùng:** dev, technical lead, triển khai.

**Nỗi đau:** yêu cầu khách có thể là cấu hình, layout, mẫu in, report, stored procedure, hoặc code; sửa sai chạm báo cáo khác, view GetData, hạn thanh toán, tồn kho, công nợ.

**AI hỗ trợ:** phân loại yêu cầu thành `config/layout/report/procedure/code`; lập impact map bảng/view/procedure/report; đề xuất test regression; nhắc quy tắc đặt tên và log.

**Đo giá trị:** giảm bug do chỉnh sửa; giảm thời gian phân tích impact; tăng chất lượng release note.

### USP-4: BRAVO Testcase Copilot

**Người dùng:** QA, BA, dev.

**Nỗi đau:** testcase nghiệp vụ phải phủ vai trò, dữ liệu, ngoại lệ, quyền, duyệt, khóa dữ liệu, số dư, lô/serial, offline sync.

**AI hỗ trợ:** sinh bộ testcase từ KQPT: happy path, exception, permission, audit, report reconciliation; gợi ý dữ liệu mẫu.

**Đo giá trị:** tăng coverage; giảm lỗi lọt production; giảm thời gian viết test.

### USP-5: User Guide & Helpdesk Copilot

**Người dùng:** support, tư vấn, key user, end user.

**Nỗi đau:** user guide dài, người dùng không biết tên chức năng; support hỏi lặp lại; tri thức nằm ở tài liệu và người lâu năm.

**AI hỗ trợ:** hỏi đáp theo ngôn ngữ tự nhiên, dẫn đến đúng menu/chứng từ/bước thao tác; từ chối khi thiếu căn cứ; tạo "phiếu hướng dẫn" theo vai trò.

**Đo giá trị:** % ticket tự phục vụ; thời gian phản hồi; satisfaction của key user.

### USP-6: BRAVO Voucher Assistant

**Người dùng:** kế toán mua hàng, bán hàng, kho.

**Nỗi đau:** nhập chứng từ, map hóa đơn, đối chiếu PO/lệnh nhập/QC, phân bổ chi phí, theo dõi hạn thanh toán còn tốn công.

**AI hỗ trợ:** tạo draft chứng từ đúng loại BRAVO, preview hạch toán, verify số, gắn nguồn kế thừa, cảnh báo thiếu căn cứ.

**Đo giá trị:** số chứng từ/giờ; % draft duyệt-không-sửa; lỗi nhập liệu giảm.

### USP-7: Management Dashboard Explainer

**Người dùng:** quản lý, CFO, giám đốc, trưởng bộ phận.

**Nỗi đau:** dashboard nhiều chỉ tiêu nhưng người dùng vẫn phải hiểu công thức, nguồn dữ liệu, biến động.

**AI hỗ trợ:** giải thích chỉ tiêu, truy nguồn báo cáo, so sánh kỳ, chỉ ra bất thường nhưng không tự kết luận khi thiếu căn cứ.

**Đo giá trị:** giảm thời gian hỏi kế toán/BI; tăng số báo cáo tự phục vụ.

### USP-8: Governance & Audit Copilot

**Người dùng:** kế toán trưởng, kiểm soát nội bộ, admin.

**Nỗi đau:** phân quyền, log, khóa dữ liệu, duyệt chứng từ, thay đổi layout/report rất khó kiểm soát thủ công.

**AI hỗ trợ:** đọc audit log, giải thích thay đổi, phát hiện chứng từ/draft/permission bất thường, tạo cảnh báo chờ người xử lý.

**Đo giá trị:** giảm thời gian audit; tăng khả năng truy vết; giảm rủi ro phân quyền sai.

## 5. Ma trận ưu tiên

| Ưu tiên | USP | Vì sao trước |
|---|---|---|
| P0 | User Guide & Helpdesk Copilot | rủi ro thấp, không cần ERP API, tận dụng ngay 19 user guide + KQPT + technical doc |
| P0 | Implementation Copilot | đúng nhu cầu nội bộ BRAVO, giảm tải support/triển khai, tạo pilot thật nhanh |
| P1 | BA/PTNV Copilot | tăng năng suất đội phân tích và tạo dữ liệu chuẩn cho dev/test |
| P1 | Customization Impact Copilot | USP mạnh vì dựa trên schema/quy trình BRAVO, generic AI khó làm đúng |
| P1 | Testcase Copilot | dễ đo bằng coverage và bug lọt, hỗ trợ trực tiếp chất lượng phần mềm |
| P2 | Voucher Assistant | giá trị lớn nhưng cần schema chứng từ/draft đúng BRAVO và guardrail mạnh |
| P2 | Dashboard Explainer | cần metric/catalog nguồn dữ liệu chuẩn |
| P3 | Governance & Audit Copilot | cần audit log/ERP data thật để có giá trị sâu |

## 6. Lộ trình đề xuất

### Giai đoạn A — Knowledge pilot nội bộ

Nạp corpus:

- 19 mindmap.
- User guide PDF/DOCX.
- Tài liệu khối kỹ thuật.
- Bộ KQPT/PTNV.
- Basic rules, dashboard, file attached, mẫu in, notification, offline mobile.

Năng lực:

- Hỏi đáp có trích dẫn.
- Tóm tắt quy trình theo vai trò.
- Tìm tài liệu/chức năng liên quan.
- Từ chối khi không có nguồn.

Eval:

- 50 câu hỏi support/triển khai thật.
- 30 câu hỏi BA/PTNV thật.
- 20 câu hỏi dev schema/config thật.

### Giai đoạn B — Lifecycle copilot

Thêm workflow có cấu trúc:

- Sinh checklist khảo sát.
- Sinh impact analysis.
- Sinh testcase.
- Sinh hướng dẫn user theo chức năng.
- Sinh escalation packet cho ticket khó.

Guardrail:

- Mọi câu trả lời phải trích nguồn.
- Không tự khẳng định schema nếu không có tài liệu.
- Không sinh SQL/update trực tiếp.

### Giai đoạn C — ERP-aware copilot

Khi có ERP API/view/catalog:

- Đọc số liệu và trạng thái chứng từ.
- Drill-down tới chứng từ nguồn.
- Tạo draft chứng từ/kiến nghị chờ duyệt.
- Soát phân quyền, audit, khóa dữ liệu.

## 7. Điều chỉnh định vị sản phẩm

Định vị cũ: **Finance AI Copilot / AP money-engine**.

Định vị nên mở rộng:

> **BRAVO AI Copilot là trợ lý triển khai, hỗ trợ và vận hành ERP BRAVO có hiểu nghiệp vụ, schema và quy trình kiểm soát của BRAVO; giúp đội BRAVO và khách hàng tra cứu, phân tích, kiểm thử, hướng dẫn, tạo nháp nghiệp vụ nhanh hơn nhưng vẫn có nguồn, có quyền, có người duyệt.**

Nói ngắn cho lãnh đạo:

> **Không chỉ hỏi số liệu kế toán. Đây là lớp AI giúp BRAVO triển khai nhanh hơn, hỗ trợ khách tốt hơn, và giúp người dùng thao tác ERP ít sai hơn.**

## 8. Các việc cần làm tiếp trong repo

1. Mở rộng ingestion/eval để corpus kỹ thuật/KQPT được coi là nguồn tri thức hạng nhất.
2. Dùng [BRAVO-KB-TAXONOMY-EVAL.md](BRAVO-KB-TAXONOMY-EVAL.md) làm chuẩn `source_type`, metadata, query routing và hard gates cho Demo A.
3. Duy trì playbook prompt mode tại [../file_system/bravo_lifecycle_playbooks.yaml](../file_system/bravo_lifecycle_playbooks.yaml) cho `implementation_support`, `ba_support`, `technical_impact`, `qa_testcase`, `support_helpdesk`, `voucher_assistant`, `dashboard_explainer`, `governance_audit`.
4. Dùng [../file_system/bravo_ai_use_cases.yaml](../file_system/bravo_ai_use_cases.yaml) làm ma trận ưu tiên use-case: P0 knowledge/helpdesk/implementation, P1 BA-impact-test-support, P2 voucher/dashboard, P3 governance.
5. Xây bộ câu hỏi eval nội bộ theo 4 nhóm: user guide/support, triển khai kỹ thuật, BA/PTNV, guardrail nghiệp vụ.
6. Thiết kế schema draft theo chứng từ BRAVO trước khi mở rộng AP automation.
