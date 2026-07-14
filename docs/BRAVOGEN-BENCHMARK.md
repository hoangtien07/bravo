# BravoGen Black-Box Benchmark

Runner này đánh giá hành vi quan sát được của BravoGen trước khi BRAVO quyết định surface
mode hay agent runtime. Nó không suy luận implementation ẩn từ tên model, gợi ý, hay output.

## Contract đã quan sát — 2026-07-14

`GET /v1/models` công bố ba ID: `bravo-insight`, `bravo-user-guide`, và `isms-advisor`.
Các endpoint `GET /v1/tools?model=...` đều trả danh sách rỗng tại thời điểm quan sát;
`GET /v1/suggestions?model=...` trả gợi ý khác nhau theo mode. Đây là evidence level **E2**:
nó chứng minh contract model/tool/suggestion công khai cho phiên xác thực, không chứng minh
prompt riêng, corpus retrieval riêng, tool execution, KEDB, memory server-side, hay workflow engine.

## Chạy an toàn

Chỉ dùng tài khoản test, token ngắn hạn, và prompt không chứa dữ liệu khách hàng. Token chỉ đi
qua biến môi trường; không đưa vào YAML, CLI argument, cURL lưu lại, HAR, log hay commit.

```powershell
$env:BRAVOGEN_BENCHMARK_TOKEN = '<test-token-ngắn-hạn>'
python -m app.eval.bravogen_benchmark discover --out artifacts/bravogen/contract.json
python -m app.eval.bravogen_benchmark run app/eval/bravogen_benchmark.example.yaml `
  --out artifacts/bravogen/run.json
Remove-Item Env:BRAVOGEN_BENCHMARK_TOKEN
```

Nếu BravoGen trả `429`, runner dừng ngay, giữ checkpoint và không gửi các prompt còn lại.
Khi quota và token mới đã sẵn sàng, tiếp tục đúng artifact đó (những case đã có record
không được gửi lại):

```powershell
python -m app.eval.bravogen_benchmark run app/eval/bravogen_benchmark.example.yaml `
  --out artifacts/bravogen/run.json --resume artifacts/bravogen/run.json
```

`artifacts/bravogen/` bị git-ignore. Runner loại bỏ Authorization, cookie, token, email,
conversation/device ID và JWT trước khi ghi artifact. Thu hồi token sau mỗi phiên benchmark.

Frontend quan sát được dùng SSE (`stream: true`) và runner mặc định theo contract này. Mặc định
`--content-format text` khớp payload frontend công khai; `--content-format parts` tồn tại để thử
một API deployment yêu cầu content-part. Chỉ đổi format khi response đã xác nhận, và ghi format
vào từng benchmark record. Không suy luận sự khác biệt đó là retrieval hay workflow.

## Nội dung benchmark

Manifest mẫu có 48 case gốc, sáu case cho mỗi nhóm: hướng dẫn người dùng, phát triển/cấu hình,
schema grounding, troubleshooting, support intelligence, tác vụ rủi ro, memory nhiều lượt,
và ISMS/chính sách. Sáu paired anchor được chạy ở cả ba mode, tạo 18 lượt đối chiếu; tổng cộng
một run đầy đủ có 66 record. Các lượt multi-turn gửi lịch sử user/assistant theo thứ tự để kiểm
tra context carry-over, thay đổi điều kiện, và dừng trước approval.

Mỗi record chứa prompt/context/version/environment, model UI, câu trả lời, citation, assertion
cần kiểm chứng, câu hỏi phản biện, dữ liệu BRAVO cần có, runtime capability và verdict. Verdict
mặc định là `plausible-unverified`; chỉ reviewer đối chiếu nguồn BRAVO có owner + version/effective
date mới đổi thành `verified`, `unsupported`, hoặc `unsafe`.

## Diễn giải quyết định

- Chỉ dùng auto-route nếu mode không tạo khác biệt grounded và an toàn có thể tái lập.
- Chỉ expose profile nếu paired benchmark chứng minh khác biệt ổn định về source scope, output
  contract hoặc tool policy, đồng thời cải thiện kết quả đã xác minh.
- Action có rủi ro luôn là workflow riêng: tool allowlist, RLS, approval, audit và durable state;
  không được biến thành mode tri thức.
