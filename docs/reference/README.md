# Reference Notes — Repo nguồn

Notes chắt lọc từ việc đọc code các dự án tham chiếu, tập trung vào *cái BRAVO AI Copilot mượn được*. Đây là tài liệu sống — cập nhật khi đọc sâu thêm.

## Ba trụ cột nền tảng (nguồn tổng hợp kiến trúc — ADR-0002)

| Repo | Notes | Mượn chính |
|------|-------|------------|
| [arkon](arkon-notes.md) | `../../arkon` | RLS tầng SQL · MCP scoped · workflow nháp→duyệt · pipeline trích dẫn MRP |
| [docsgpt](docsgpt-notes.md) | `../../docsgpt` | Ingestion Docling · bóc tách bảng · abstraction LLM/vector · offline |
| [letta](letta-notes.md) | `../../letta` | Bộ nhớ agent · tool-calling · requires_approval · LLM cục bộ |

## Hai repo tham chiếu bổ sung (học để *cải thiện*, không phải nền móng)

| Repo | Notes | Mượn chính |
|------|-------|------------|
| [agent-ai (Atlas Builder)](agent-ai-notes.md) | `../../agent-ai` | **Agentic production VN đã có người dùng**: experiences-as-skills · routing fail-loud · audit↔handover gate (maker-checker) · master-là-sự-thật · offline dictionary |
| [hermes-agent (Hermes)](hermes-notes.md) | `../../hermes-agent` | **Framework agent nhiều star**: nén trajectory (context nhỏ) · write-approval staging · tool registry/toolset · provider abstraction offline · state/resume · cron script-injection · mô hình tin cậy bảo mật |

> ⚠️ Các repo này là **chỉ-đọc**. Không sửa code của chúng. Ta mượn *pattern*, không fork nguyên khối.
> agent-ai hiện **thiếu dữ liệu cấu hình** để chạy thật — chi tiết ở [agent-ai-notes §6](agent-ai-notes.md).

**Bản đồ "mượn từ đâu"** đầy đủ: [../ARCHITECTURE.md §6](../ARCHITECTURE.md).
