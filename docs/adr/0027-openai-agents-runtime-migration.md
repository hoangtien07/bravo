# 0027. Di trú runtime sang OpenAI Agents SDK theo canary

**Trạng thái:** Accepted  
**Ngày:** 2026-07-13

## Quyết định

BRAVO dùng OpenAI Agents SDK trên Responses API cho runtime frontier mới. Việc di trú theo
feature flag `AGENT_RUNTIME=legacy|canary|openai`; runtime legacy tiếp tục là fallback cho đến
khi canary vượt bộ eval nghiệp vụ.

Postgres BRAVO vẫn là nguồn chuẩn cho hội thoại, RLS, audit, draft và approval. Agents SDK không
được phép thay thế các kiểm soát này hoặc được cấp tool truy cập trực tiếp vào database/ERP.

## Lý do

SDK cung cấp loop, streaming, sessions, tool calling, HITL pause/resume, tracing và Realtime đã
được duy trì công khai. Tuy vậy, migration không được gộp với lỗi retrieval hiện tại: corpus
routing phải lọc metadata trong SQL trước hybrid retrieval, không chỉ boost sau khi tìm toàn bộ
corpus.

## Hệ quả

- Pin chính xác `openai-agents==0.17.4`; mọi nâng version phải qua streaming, HITL và RLS suite.
- Canary đầu tiên chỉ chạy lượt text-only, không tool/write/multimodal; attachment vẫn dùng loop
  legacy để không làm mất provenance.
- Tracing SDK tắt mặc định. Audit và OTel của BRAVO là kênh quan sát chuẩn.
- Full GraphRAG chỉ được làm sau benchmark quan hệ đa tài liệu, không phải cơ chế vá truy hồi
  chọn sai corpus.
