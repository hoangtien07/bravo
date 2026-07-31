# 0032. Demonstrator sâu đầu tiên của V2 = Reconciliation & Exception Investigator

- **Trạng thái:** **Accepted** (2026-07-31) — chủ dự án xác nhận trong phiên rà soát product scope.
- **Ngày:** 2026-07-31
- **Người quyết định:** Chủ dự án.
- **Căn cứ:** [Frontier BRAVO Accounting Agent plan](../../plan-rebuild/10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md),
  capability map từ tài liệu BRAVO 10, council kế toán/kiểm soát/sản phẩm/kiến trúc và phản biện
  product scope ngày 2026-07-31.
- **Supersedes trong phạm vi chọn demonstrator V2:** [ADR-0016](0016-pivot-standalone-ap-vertical.md)
  và đề xuất [ADR-0031](0031-first-pilot-ap-vertical-gate.md).
- **Không supersede:** các invariant deterministic, number integrity, no-free-form-SQL,
  maker-checker, draft-first và non-invasive của ADR-0016 cùng các ADR liên quan.

## Bối cảnh

Các tài liệu gần đây đã biến Financial Close Advisor từ một nhóm câu hỏi benchmark thành mục tiêu
sản phẩm. Điều này không phản ánh ý định của chủ dự án: mục tiêu cuối của `Công việc AI` là một
frontier accounting agent cho BRAVO, còn Financial Close chỉ là một tình huống nghiệp vụ.

Đồng thời, ADR-0016 Accepted đang chọn Copilot AP làm mũi nhọn đầu tiên và ADR-0031 Proposed tiếp
tục chọn AP cho pilot. Vì không có ADR supersede, kế hoạch Financial Close đã tạo ra hai nguồn sự
thật xung đột.

Sau khi đọc lại hướng dẫn BRAVO 10, council xác nhận BRAVO đã có chứng từ, định khoản, mua hàng,
HĐĐT đầu vào, đối trừ, tính giá, cuối kỳ, khóa sổ, phê duyệt, task, báo cáo và audit. Demonstrator
AI không được làm lại các chức năng đó. Nó phải chứng minh phần giá trị bổ sung: tập hợp evidence
liên hệ thống, đối soát tất định, điều tra ngoại lệ mơ hồ, giải thích có lineage và đề xuất hành
động để người có thẩm quyền xem xét.

## Quyết định

Chọn **Reconciliation & Exception Investigator** làm demonstrator sâu đầu tiên của Conversation /
AccountingCase Core V2.

Phạm vi quyết định:

1. Đây là demonstrator đầu tiên để kiểm chứng kiến trúc, chất lượng hội thoại và outcome kế toán.
   Nó chưa phải quyết định về first paid pilot, SKU hoặc toàn bộ định vị sản phẩm.
2. Financial Close Readiness được giữ làm benchmark family và một Periodic Accounting case
   template; không còn là product root.
3. Copilot AP/Voucher Evidence Review được giữ trong capability portfolio; không còn là
   demonstrator V2 mặc định.
4. Product north star vẫn là **BRAVO Accounting Intelligence** gồm Knowledge Chat và Accounting
   Operations Hub, không phải một sản phẩm reconciliation đơn lẻ.

Chủ dự án xác nhận tiếp ngày 2026-07-31: subtype đầu tiên là **Bank statement ↔ sổ tiền gửi
BRAVO**. Demo dùng versioned synthetic fixtures; việc chọn subtype không cho phép truy cập dữ liệu
khách hàng hoặc suy diễn BRAVO API đã tồn tại.

## Contract của demonstrator

### Outcome

Từ hai hoặc nhiều bộ dữ liệu đã được phê duyệt, hệ thống tạo một reconciliation case có scope cố
định, kết quả match chính xác, danh sách ngoại lệ có evidence/lineage, giải thích hữu ích và bước
xử lý được đề xuất để người dùng review.

Subtype đầu tiên nhận hai nguồn:

- sao kê ngân hàng đã chuẩn hóa theo schema/version được freeze;
- sổ tiền gửi hoặc supported export tương ứng từ BRAVO theo cùng tài khoản, pháp nhân, tiền tệ và
  cutoff.

Engine phân loại tối thiểu: exact match, tolerance match, aggregated candidate, duplicated,
bank-only, BRAVO-only và ambiguous. Tên nhóm có thể đổi khi freeze glossary nhưng ý nghĩa và golden
answer không được model quyết định.

### User và buyer hypothesis

- User ban đầu: kế toán lập đối soát và người review/kế toán trưởng.
- Buyer hypothesis: kế toán trưởng hoặc controller.
- Đây là giả thuyết discovery, chưa phải bằng chứng willingness-to-pay.

### Deterministic core bắt buộc

- khóa tenant/legal entity/book/period/cutoff/currency/version;
- source coverage và completeness;
- normalization, matching, aggregation và reconciliation;
- tolerance/materiality policy do cấu hình đã duyệt cung cấp;
- reason codes, exception severity và lineage;
- state machine, idempotency, queue và audit;
- payload-bound maker-checker cho mọi draft action/export.

### LLM được phép

- hỏi dữ kiện kinh doanh còn thiếu;
- đề xuất mapping key cho trường hợp mơ hồ;
- giải thích vì sao một item unmatched hoặc potentially matched;
- nhóm ngoại lệ có ngữ nghĩa gần nhau;
- soạn investigation note và next-step narrative có evidence.

### LLM bị cấm

- tính hoặc sửa số authoritative;
- tự đặt tolerance/materiality;
- xác nhận đã reconcile khi deterministic engine chưa chứng minh;
- waive/approve ngoại lệ;
- post adjustment, ghi sổ, thanh toán, khóa kỳ hoặc chạy SQL/query tùy ý.

## Phạm vi demo

- synthetic, single tenant, không dữ liệu khách hàng;
- API-independent bằng versioned file fixtures ở bước đầu;
- read-only outcome; draft/export chỉ là payload có review;
- không Keycloak/OIDC và không production claim;
- một Accounting Work inbox, một case page hoàn chỉnh;
- Voucher Evidence Review và Period Close Readiness chỉ được dùng làm preview có nhãn nếu cần
  chứng minh breadth;
- Governance & Integration chỉ có BA specification, FE mock và configuration-as-code.

## Phương án đã cân nhắc

| Phương án | Kết luận |
|---|---|
| Financial Close Advisor | Không chọn làm product/demonstrator root; đây là benchmark/template |
| Copilot AP | Giữ làm capability candidate; BRAVO đã có nhiều chức năng invoice/voucher nên cần coverage audit để tránh trùng |
| Management Variance Investigator | Giá trị quản trị tốt nhưng phụ thuộc semantic/lineage đáng tin cậy chưa có |
| Reconciliation & Exception Investigator | **Chọn**: ranh giới deterministic/LLM rõ, outcome đo được, bổ sung cross-source investigation thay vì làm lại ERP |
| Nhiều capability deep song song | Không chọn: làm loãng bằng chứng và tăng bề mặt dữ liệu/kiểm soát trước khi một case qua gate |

## Hệ quả

### Tích cực

- giải quyết xung đột AP-versus-Close cho demonstrator V2;
- có bài toán mà số liệu và match có thể kiểm thử tất định;
- chất lượng LLM được đánh giá đúng ở ambiguity, explanation và missing-context handling;
- dùng lại được `AccountingCase`, evidence snapshot, finding, review và trace cho capability sau;
- tránh dựng lại voucher, close engine hoặc task manager của BRAVO.

### Chi phí và giới hạn

- phải xây deterministic reconciliation contract và golden fixtures trước khi tối ưu prompt;
- cần định nghĩa scope, completeness, tolerance, materiality và false-negative severity cho từng
  reconciliation type;
- chưa chứng minh buyer, willingness-to-pay, API coverage hoặc production topology;
- không được suy diễn demonstrator thành quyết định first paid pilot.

## Gate trước implementation

1. Hoàn tất runtime containment và freeze matched A/B baseline.
2. **Hoàn thành:** subtype đầu tiên là Bank statement ↔ sổ tiền gửi BRAVO.
3. Freeze source schema, scope key, rule/tolerance policy và SME answer key.
4. Có golden matched/unmatched/potentially-matched cases, including critical false negatives.
5. Chứng minh deterministic engine không phụ thuộc LLM.
6. Chỉ sau đó mới thêm bounded LLM slots và chạy blind SME evaluation.

## Gate chưa được quyết định

- reference deployment cho pilot;
- real-data model/egress policy;
- BRAVO API/export contract cho pilot;
- paid-pilot buyer và packaging;
- capability tiếp theo sau reconciliation.
