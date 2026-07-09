# Findings N — Agent AI có end user thật và cách tối ưu công việc

> Ngày quét: 2026-07-09. Mục tiêu: mở rộng sau Findings L/M, tập trung vào các bài phân tích/case có người dùng thật hoặc dữ liệu production, để rút ra cách agent AI được tối ưu cho công việc thật. Không nhằm mở rộng scope agent mới cho BRAVO; chỉ dùng để cải thiện cách chọn workflow, eval, pilot và UX.

## 1. TL;DR

Các case có bằng chứng tốt nhất không phải "agent tự do làm mọi thứ", mà là **agent bị đóng vào một lát cắt công việc rõ**, có dữ liệu/ngữ cảnh tốt, có workflow/handoff, có eval trước production, rồi đo bằng metric vận hành.

Mẫu lặp lại:

1. **Customer support/service desk là nơi agent có user thật nhiều nhất.** Nubank, Alibaba, ServiceNow, YBS, Intercom/Fin đều tập trung vào hỗ trợ khách hàng, case resolution, complaint handling, policy search, summary, draft response.
2. **Agent hiệu quả nhất khi giảm việc chuyển màn hình/tìm policy/tóm tắt/draft**, không nhất thiết tự ra quyết định cuối. YBS tiết kiệm 7-26 phút/case bằng summary, policy search, draft dưới human oversight.
3. **Eval-driven development là lõi production.** Nubank nhấn mạnh chất lượng eval quyết định tốc độ iteration; dùng context engineering, prompt versioning, human-in-loop prompt iteration, LLM judge có kiểm inter-rater, A/B test online.
4. **HITL phải thiết kế theo loại lỗi, không chỉ có nút "escalate".** Alibaba cho thấy agentic AI giảm thời lượng chat nhưng có thể làm giảm rating ở AI-eligible chats; can thiệp sớm giúp technical escalations, nhưng emotional escalations khó hơn nếu người giám sát vào muộn hoặc ít nỗ lực.
5. **AI giúp low/novice users mạnh hơn expert users.** Các field experiment customer support cho thấy nhân sự ít kinh nghiệm/lower-performing hưởng lợi lớn; expert/top performers có thể ít lợi hoặc giảm chất lượng nếu multitask quá mức.
6. **Workflow hardened > on-the-fly agent.** Paper AI Workflow Store cảnh báo agent tự tổng hợp plan/toolchain tức thì dễ thành "prototype ứng biến"; high-stakes nên dùng workflow đã test, version, staged deployment.
7. **Back-office/finance automation có bằng chứng tốt khi quy trình là IDP + rule/policy DB + exception + HITL + learning.** Case corporate expense processing báo cáo giảm >80% thời gian xử lý biên lai giấy, nhưng vẫn có human final decision.

## 2. Source matrix

| source_id | source | real user/data | work optimized | measured result | mechanism | relevance to BRAVO |
|---|---|---|---|---|---|---|
| N1 | [Nubank customer support agents at 100M-user scale](https://arxiv.org/abs/2606.08867) | 100M+ users, five production deployments | Card delivery, debt, credit-limit, card management, product explanation | Card delivery +37 pp AI tNPS, +29 pp self-service vs prior variants; AI satisfaction near expert human in most use cases | Modular context engineering, HITL prompt iteration, calibrated judge, A/B tests | Strong template for eval-driven BRAVO pilot |
| N2 | [Perplexity Computer production-data study](https://arxiv.org/abs/2606.07489) | Production data from Search/Computer | Knowledge work task decomposition/execution | 26 min autonomous work/session vs 33 sec Search; matched completion time 269 -> 36 min; dissatisfaction -55% | Agent does bundled subtasks, user shifts to verification/extension | Useful for "agent should do prep work"; weak for finance safety |
| N3 | [Yorkshire Building Society AI agents](https://www.itpro.com/business/business-strategy/yorkshire-building-society-touts-customer-service-gains-with-ai-agents) | Real financial-services staff, complaint/customer support | Summarize complaints, search policies/past cases, draft member communications | Sam saves ~7 min/use; Penelope up to 26 min on complex complaints; risk/control pilot ~40% efficiency saving | Human oversight, data/governance foundations, 360-degree customer view | Very relevant UX pattern for BRAVO support/accounting review |
| N4 | [Intercom/Fin analysis via Vox](https://www.vox.com/technology/474380/chatgpt-openai-google-gemini-ustomer-service) | Production customer service | AI resolves customer issues | Reported 1M queries/week, 67% resolution; needs human for some interactions | Heavy evaluation engine, release torture-tests, instant resolution | Shows eval + resolution metric matter; vendor-side figures |
| N5 | [Alibaba agentic AI + HITL field experiment](https://arxiv.org/abs/2605.14830) | Randomized field experiment on Taobao | AI-eligible service chats + human supervision | Reduces average chat duration; limited retrial impact; lowers ratings for AI-eligible chats | Intervention timing/type matters; technical vs emotional escalations differ | Warning: HITL design must preserve quality, not just speed |
| N6 | [Alibaba genAI assistant field experiment](https://arxiv.org/abs/2603.29888) | Large-scale field experiment | Diagnosis and solution proposals for after-sales support | Faster issue identification/chat duration; subjective quality improves; objective retrial unchanged | Agents can adopt/modify/ignore suggestions; low performers benefit most | BRAVO should target novice/standardization first |
| N7 | [Generative AI at Work](https://arxiv.org/abs/2304.11771) | 5,172 customer support agents | Real-time response suggestions | Productivity +15%; less experienced/lower-skilled gain most; rare-problem gains | Captures tacit best practices from high performers | Useful for onboarding/support assistant and accounting review suggestions |
| N8 | [Corporate expense processing automation agent](https://arxiv.org/abs/2505.20733) | Major Korean enterprise case study | Expense processing with receipt IDP, policy classification, exception handling | >80% reduction in processing time for paper receipt tasks | OCR/IDP + policy DB + LLM exception support + HITL final decision + learning | Closest finance/back-office analogue to AP+TT99 |
| N9 | [AI Workflow Store](https://arxiv.org/abs/2605.10907) | Conceptual/architecture, not deployment | Robust personal/enterprise agent workflows | No production metric | Hardened reusable workflows over improvised on-the-fly plan execution | Strongly supports BRAVO's constrained-workflow stance |
| N10 | [MIT GenAI Divide coverage](https://www.tomshardware.com/tech-industry/artificial-intelligence/95-percent-of-generative-ai-implementations-in-enterprise-have-no-measurable-impact-on-p-and-l-says-mit-flawed-integration-key-reason-why-ai-projects-underperform) | Reported interviews/survey/deployments | Enterprise GenAI adoption | 95% no measurable P&L impact, attributed to workflow integration gaps | Specific workflow + integration beats generic pilots | Good warning against "agent demo without owner/metric" |

## 3. Cross-case patterns: agent tối ưu công việc như thế nào?

### Pattern A — "AI làm phần chuẩn bị, người làm phần quyết định"

YBS, Alibaba assistant, Generative AI at Work và AP/expense case đều hội tụ: AI tóm tắt, tìm chính sách, đề xuất câu trả lời/giải pháp, phân loại, phát hiện exception; con người giữ quyền quyết định khi rủi ro cao hoặc tình huống cảm xúc/phức tạp.

Áp dụng BRAVO:

- AP+TT99: AI parse XML, đề xuất định khoản, nêu lý do, highlight rule/citation, tạo nháp; kế toán duyệt/sửa.
- Support/implementation: AI tóm tắt ticket, tìm KQPT/PTNV/user guide liên quan, draft hướng xử lý; consultant xác nhận.
- Không nên pitch "autopost full touchless" trước khi có % duyệt-không-sửa thật.

### Pattern B — "Workflow cụ thể thắng chatbot tổng quát"

Nubank dùng năm deployment hẹp; YBS đặt tên agent theo job cụ thể; expense case có pipeline bốn bước; Workflow Store phản biện on-the-fly agents. Tất cả đều nói cùng một điều: độ tin cậy đến từ **workflow đã đóng khung**, không từ việc cho model tự phác kế hoạch mới mỗi lần.

Áp dụng BRAVO:

- Tạo **workflow cards** thay vì "agent có thể làm mọi thứ": `AP invoice draft`, `TT99 mapping review`, `support ticket summarizer`, `policy citation finder`.
- Mỗi card có input/output schema, owner, failure modes, HITL rule, metric.
- Agent loop chỉ chọn trong một tập workflow đã version, không tự bịa process.

### Pattern C — "Eval pipeline là động cơ cải tiến, không phải thủ tục cuối"

Nubank nói rõ eval quality quyết định iteration velocity; Intercom/Fin nhấn mạnh release torture-test; Alibaba cho thấy online effects có thể khác metric offline nếu đo thiếu satisfaction/retrial/emotional failure.

Áp dụng BRAVO:

- Với mỗi workflow card cần có `offline golden set -> human review -> pilot A/B or before/after -> production metric`.
- Không chỉ đo "answer đúng"; đo `time saved`, `% duyệt không sửa`, `unsupported claim`, `escalation reason`, `user correction taxonomy`.
- Eval phải tách novice/expert users vì AI có thể giúp người mới nhưng làm expert multitask quá mức.

### Pattern D — "HITL cần timing và context preservation"

Alibaba agentic HITL cho thấy can thiệp sau escalation không tự động cứu chất lượng; technical escalations dễ cứu hơn emotional escalations. Nubank cũng nhấn mạnh handoff phải giữ full context.

Áp dụng BRAVO:

- Với AP, escalate sớm khi thiếu chứng từ/rule conflict, không để agent đi tiếp rồi mới trả một draft mơ hồ.
- Handoff cho kế toán phải có: input gốc, rule đã áp, lý do đề xuất, confidence/failure tag, citations, exact cells/fields.
- Sửa của người dùng phải trở thành feedback event để cải thiện coding/rules, không chỉ là edit UI.

### Pattern E — "Tối ưu cho adoption bằng công việc đã có tần suất cao"

Các case thành công gắn vào luồng đã có volume: support chats, complaints, IT tickets, expense receipts. Đây là lý do AP/e-invoice hợp với BRAVO hơn các agent hiếm gặp như IFRS conversion hay cash-flow scenario.

Áp dụng BRAVO:

- Ưu tiên workflow có nhiều lượt/ngày hoặc nhiều phút/case: upload XML hóa đơn, kiểm trùng, kiểm hợp lệ NCC, định khoản nháp, support ticket.
- Tránh demo agent trên nhiệm vụ "hay trên sân khấu nhưng hiếm trong ngày làm việc".

## 4. Implications cho BRAVO

### 4.1. Nên bổ sung vào pilot AP+TT99

| bổ sung | vì sao | metric |
|---|---|---|
| "Review cockpit" cho kế toán | Case thực tế thắng nhờ giảm context switching và chuẩn bị sẵn evidence | phút/hóa đơn; số màn hình/nguồn phải mở |
| Correction taxonomy | AI học từ sửa của người dùng, nhưng phải phân loại được sửa sai tài khoản, sai VAT, thiếu chứng từ, sai NCC | top correction reasons; % lặp lại |
| Confidence + early escalate | HITL hiệu quả khi vào sớm, không chờ output cuối | % case escalate đúng; false escalate |
| Workflow versioning | Nubank-style modular context/prompt/workflow | regression per workflow version |
| User cohort eval | AI giúp novice khác expert | metric theo kế toán mới/senior/consultant |

### 4.2. Nên bổ sung một use-case "end user thật" ngoài kế toán

Đề xuất mạnh nhất: **BRAVO Support/Implementation Ticket Copilot**.

Vì sao: repo đã có corpus user guide/KQPT/PTNV/tài liệu kỹ thuật; end users nội bộ gồm support, tư vấn triển khai, BA, QA. Workflow giống YBS/Nubank hơn là AP write-back: tóm tắt case, tìm policy/tài liệu tương tự, draft hướng xử lý, trích nguồn, human gửi khách. Rủi ro thấp hơn finance write, nhưng có user thật và volume thực.

Metric:

- phút/ticket trước-sau;
- first response time;
- % draft dùng được không sửa lớn;
- số lần phải hỏi lại dev/BA;
- citation correctness;
- hallucinated procedure = 0 hard fail.

### 4.3. Không nên đổi invariant kiến trúc

Các nguồn mới **không** ủng hộ việc nới agent tự hành trong finance. Ngược lại, chúng củng cố:

- constrained workflow;
- HITL-as-tool;
- draft trước write;
- eval-driven release;
- workflow versioning;
- narrow toolset;
- human escalation có context đầy đủ.

## 5. Updated decision notes

| current decision | update từ lượt mở rộng | verdict |
|---|---|---|
| AP+TT99 là mũi nhọn | Được củng cố vì finance/back-office workflow có tần suất và measurable value | KEEP |
| Demo chỉ chat/RAG hướng dẫn | Nên biến thành support-ticket workflow có metric người dùng thật | CHANGE/ADD |
| Single constrained agent | Được củng cố bởi Workflow Store và production cases | KEEP |
| HITL draft | Cần nâng cấp UX handoff: evidence, failure tag, confidence, correction capture | CHANGE |
| Eval pass^k/state | Cần thêm business metrics: time saved, tỉ lệ sửa tay, tNPS/internal CSAT | ADD_EVAL |
| Multi-agent/autonomous write | Không có evidence đủ; customer service còn cần careful handoff | DEFER/REJECT |

## 6. Backlog mới từ lượt này

| priority | item | description | owner area |
|---|---|---|---|
| P0 | Define AP review cockpit metrics | phút/hóa đơn, % duyệt-không-sửa, correction taxonomy, hard fail | product/eval |
| P0 | Capture user corrections as first-class events | lưu edit diff + lý do sửa để học rule/coding | app/erp/draft_queue, app/eval |
| P0 | Add early-escalation states | missing evidence, rule conflict, low confidence, unsupported citation | agent/workflow |
| P1 | Build BRAVO Support Ticket Copilot pilot | summarize ticket, retrieve docs, draft response, cite source | KB/RAG/product |
| P1 | Workflow cards registry | versioned workflow definitions with input/output schema, tests, metrics | agent/config |
| P1 | Cohort-based eval | novice vs expert accounting/support users | eval/reporting |
| P2 | A/B or before/after pilot harness | measure time/corrections/satisfaction with real users | eval/product |

## 7. Research ledger

Đã quét nhóm chủ đề:

- `AI agents real users customer support production case study`
- `agentic AI human in the loop field experiment customer service`
- `generative AI workplace field experiment customer support agents`
- `AI agents knowledge work production data autonomous work session`
- `AI workflow store hardened workflows reusable agent workflows`
- `corporate expense processing automation agent generative AI IDP case study`
- `financial services AI agents complaint handling human oversight`

Không cần quét lại rộng các chủ đề này trước khi có kết quả pilot nội bộ. Lần sau chỉ mở lại khi cần:

- case production kế toán/AP có số liệu độc lập hơn vendor;
- dữ liệu giá thật Bizzi/MISA/Agentwork tại VN;
- case ERP-embedded finance agents có audit độc lập;
- benchmark nội bộ của BRAVO cho support-ticket/AP workflows.

## 8. Bottom line

Agent AI có end user thật đang thắng ở **work prep + workflow integration + eval loop**, không phải ở autonomy tuyệt đối. Với BRAVO, quyết định hiệu quả nhất là:

1. Giữ AP+TT99 làm mũi nhọn có tiền.
2. Thiết kế review cockpit và correction loop thật tốt.
3. Thêm một pilot nội bộ ít rủi ro hơn: Support/Implementation Ticket Copilot.
4. Đo như sản phẩm vận hành: time saved, % draft dùng được, % duyệt không sửa, hard fails, user satisfaction.
