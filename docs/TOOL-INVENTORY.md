# TOOL INVENTORY — least-privilege & on-behalf-of (OWASP LLM06)

> Nguồn sự thật về **agency** của agent: mỗi tool làm gì, cần quyền gì, chạy dưới danh nghĩa
> ai. Đối chiếu OWASP LLM06 *Excessive Agency* (functionality / permissions / autonomy) và
> Findings O #8. Cơ chế đã cưỡng chế trong code ([tools.py](../app/agent/tools.py)); file này
> + [tool_inventory.py](../app/agent/tool_inventory.py) làm hợp đồng đó **tường minh & audit được**.

## Inventory hiện tại

| Tool | Chế độ | Quyền bắt buộc | Validate payload | On-behalf-of |
|---|---|---|---|---|
| `kb_search` | read | — (mở) | — | ✅ |
| `metric_lookup` | read | `metric:read` | — | ✅ |
| `preview_journal_entry` | read | `draft:create` | — (chỉ đọc draft đã dựng) | ✅ |
| `create_journal_entry` | **write → draft** | `draft:create` | ✅ Nợ=Có (payload_builder) | ✅ |

Sinh lại bảng này + chạy audit: `python -m app.agent.tool_inventory` (exit ≠0 nếu vi phạm).

## Hợp đồng least-privilege (audit gate cưỡng chế)

[audit_registry](../app/agent/tool_inventory.py) chặn (CI/pre-demo) nếu một tool vi phạm:

1. **Không ghi ẩn danh** — tool GHI phải có `required_permission` (không có = ai cũng ghi được).
2. **Ghi phải qua duyệt** — tool GHI phải `requires_approval=True`; KHÔNG bao giờ tự thực thi
   (invariant #2). `Tool.__post_init__` ép, audit bắt vật thể dựng vòng qua constructor.
3. **Ghi phải VALIDATE payload** — tool GHI phải có `payload_builder` (cổng số-liệu/luật). Draft
   ghi không kiểm ⇒ có thể mang số bịa (invariant #3). `create_journal_entry` cân Nợ=Có tại đây.
4. **Chuẩn tên quyền** `resource:action[:scope]` để `Identity.scope_level` parse được (cảnh báo).

## Mô hình on-behalf-of (chống leo thang)

Tool **không** mang danh tính riêng. [call_tool](../app/agent/tools.py) tiêm `identity` (và `db`)
của **người gọi** vào hàm tool; `json_schema` KHÔNG lộ `identity`/`db` nên LLM không thấy để chèn.
Nếu LLM cố nhét `identity` vào args, `call_tool` **ghi đè bằng identity thật** (test
`test_llm_cannot_escalate_identity_via_args`). Hệ quả:
- Read tool: RLS áp ở tầng dữ liệu theo identity người gọi (vd `metric_lookup → semantic.execute`).
- Write tool: draft gắn **đúng phòng ban người gọi** (fail-closed, không rơi về global — vá ASI03).

## Phòng thủ nhiều tầng (đã có, để tham chiếu)

- **RLS tầng 1** `filter_tools_by_permission`: tool thiếu quyền KHÔNG vào prompt → LLM không chọn được.
- **RLS tầng 2** `call_tool`: tái kiểm quyền lúc chạy (chặn tên tool giả/replay).
- **Vết** `tool_call_attempts`: mọi lần gọi (executed/drafted/failed) đều ghi `actor_id/tool/args_hash`.

## Còn thiếu / gate L3 (KHÔNG làm bây giờ)

- **Rate-limit per-tool per-identity** (chống lạm dụng tool đọc tốn kém) — có rate-limit HTTP,
  chưa có mức per-tool.
- **Tool MCP ngoài**: khi mount MCP, schema phải pin/validate server-side (tool-poisoning
  MCPoison/CurXecute); audit này cần mở rộng phủ tool MCP đã mount.
- **Autonomy budget** (số bước/tool mỗi lượt) — đã có Budget trong loop; chưa nối vào audit.
