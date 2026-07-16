# P0-03 — Mode boundary analysis

Status: `COMPLETE FOR OBSERVED SAMPLE — cross-mode and mode-profile runs recorded`

Phân tích T01, T02 và T20. Không coi mode label hoặc lời tự mô tả là bằng chứng tách corpus/tool.

| Finding ID | Finding | Type | Supporting tests | Counter-evidence | Confidence |
|---|---|---|---|---|---|
| MB-001 | Cả User Guide và ISMS đều từ chối câu hỏi Layout XML và điều hướng sang Bravo Insight; Insight nhận domain nhưng abstain vì nói không tìm thấy tài liệu. | OBSERVED | T01.2, ba mode, run 1 | Chưa lặp ở phiên độc lập; prompt có nêu rõ không suy đoán nên có thể làm tăng refusal | Medium |
| MB-002 | Ba mode có policy/persona boundary khác nhau ở tầng phản hồi. | INFERRED | T01.2, ba mode, run 1 | Chưa chứng minh corpus/tool/authorization tách biệt | Medium |
| MB-003 | Ba mode có corpus hoặc tool permission riêng. | UNVERIFIED | Tự thuật của chatbot; hành vi T01.2 phù hợp nhưng không đủ phân biệt | Cùng model/prompt có thể tạo hành vi giống hệt | Low |

## Wave 7/8 update

T02 and T20.1-T20.3 add 12 valid cross-mode observations. User Guide and ISMS consistently redirect technical or operational requests outside their surface; Insight answers or abstains with a different contract. This raises the behavioral-boundary finding to `OBSERVED` with high confidence, while corpus/tool/authorization separation remains `UNVERIFIED`. See `P0-18-cross-mode-controls.md` and `P0-19-repeat-controls.md`.

## Preliminary interpretation

T01.2 xác nhận **product behavior** mong đợi của ba profile trên một câu kỹ thuật. Nó chưa xác nhận router trung tâm: người dùng tự chọn mode trước khi gửi, và hai mode ngoài phạm vi chỉ có thể đang áp dụng một instruction/template điều hướng.

Bravo Insight nói đã tra cứu tài liệu nhưng không có trace/citation/tool event quan sát được. Execution claim này vẫn là `UNVERIFIED`.
