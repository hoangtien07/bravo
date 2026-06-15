# BRAVO Chat — Frontend (React SPA)

Nền tảng chat cho BRAVO AI Copilot. React 18 + Vite + TypeScript + Tailwind (design tokens
brand BRAVO, primitives kiểu shadcn). Học pattern từ docsgpt (SSE/conversation) — bỏ phần
over-engineered (Redux, message-events-journal, compaction).

## Chạy
```bash
npm install
npm run dev      # http://localhost:5173 (proxy /api -> http://localhost:8000) — cần backend chạy
npm run build    # -> dist/ (FastAPI serve ở /static + SPA-fallback, base=/static/)
```

## Cấu trúc
```
src/
  api/        client (fetch+JWT+401) · sse (drainSse: POST+ReadableStream) · types
  store/      auth (Zustand) · chat (streaming buffer + send/abort)
  components/ ui (Button/Input/Card/Badge/Spinner — kiểu shadcn)
  features/
    auth/     LoginPage
    chat/     AppShell · ConversationSidebar · ChatView · MessageBubble (markdown+steps+badges)
              Composer (Enter gửi) · DraftCard (bút toán inline approve/reject)
    money/    MoneyEnginePage (upload hoá đơn XML hàng loạt -> DraftCard)
    shared/   SharedPage (xem hội thoại chia sẻ read-only)
```

## Luồng streaming
`Composer.send` → `store/chat.send` → `api/sse.streamChat(POST /api/chat/{id}/messages)` →
parse SSE event `{id,source,step,tool_call,tool_result,draft,answer,done,error}` → cập nhật
message tăng dần (answer chunk · agent steps · citations · DraftCard inline). Hủy bằng AbortController.

## Backlog
true token-streaming · httpOnly cookie auth (hiện sessionStorage) · thả hoá đơn trong composer ·
dark theme · code-split bundle.
