# Knowledge Chat API V1 — Plan 18 frozen frontend contract

Status: `LOCAL SYNTHETIC INTERNAL DEMO CONTRACT`

This document freezes the existing FastAPI conversation interface for the FigmaMake candidate.
It does not create a second protocol and is not a production compatibility guarantee.

## Authorization and scope

- Candidate session token is sent as `Authorization: Bearer <token>` for protected routes.
- Conversation ownership is enforced by the server. A non-owner receives a scoped unavailable response; the client must not infer existence.
- `GET /api/shared/{token}` is unauthenticated and renders a read-only transcript without the authenticated shell.
- The client maps `401`, `403`, `404`, `409`, `422`, `429`, `5xx` and network loss to recoverable states. It never turns a failure into an empty list or completed answer.

## Conversation resources

| Operation | Request | Success payload fields consumed by FigmaMake |
|---|---|---|
| List | `GET /api/conversations` | `id`, `title`, `last_message_at`, `created_at` |
| Detail | `GET /api/conversations/{id}` | `id`, `title`, `messages[]` |
| Rename | `POST /api/conversations/{id}/rename` with `{title}` | Conversation detail |
| Delete | `DELETE /api/conversations/{id}` | `204` |
| Feedback | `POST /api/conversations/{id}/messages/{messageId}/feedback` with `{value}` | `204` |
| Share / revoke | `POST` / `DELETE /api/conversations/{id}/share` | `shared_token`, `url` on POST |
| Shared read | `GET /api/shared/{token}` | `title`, `messages[]` |

`messages[]` is strict: `id`, `role` (`user` or `assistant`), `content`, `created_at`, and `feedback` (`like`, `dislike`, or `null`). Invalid success payloads are visible contract errors, not guessed projections.

## POST-SSE turn

`POST /api/chat/{conversationId}/messages` accepts `question`, `attachment_ids`, `source_ids`, `mode`, `web_access`, `consultant_mode`, and `consultant_profile`. The candidate sends `mode: auto`, `web_access: off`, and the existing auto consultant settings.

The client uses `fetch` and `ReadableStream`, not `EventSource`, because the request requires a bearer header. The parser accepts CRLF/LF records, fragmented chunks and multiple records; ignores comments; isolates malformed records as a visible stream error; and honours abort.

Known event types are `id`, `plan`, `plan_update`, `source`, `attachments`, `status`, `step`, `tool_call`, `tool_result`, `artifact`, `draft`, `answer`, `done`, `error`, and `ping`.

| Event | Fields used | Candidate behavior |
|---|---|---|
| `answer` | `delta` | Append to ephemeral assistant placeholder. |
| `source` | `citations[]` | Populate Evidence Rail with server labels only. |
| `done` | `citations[]`, `grounded`, message IDs | Replace rail state and refetch durable transcript. |
| `error` | `code`, `message` | Preserve partial stream as incomplete and show recoverable error. |

Unsupported events are not terminal success. The UI never renders tool internals or chain-of-thought. A normal terminal path is a `done` event followed by a durable `GET` refetch.

## Governed evidence endpoints

- `POST /api/attachments` uses multipart `file`; response fields are `id`, `filename`, `mime_type`, `size_bytes`, `kind`, `status`, `token_count`, `error`.
- `GET` / `DELETE /api/attachments/{id}` are owner-scoped.
- `GET /api/sources` returns authorized rows with `id`, `filename`, `status`, `knowledge_type`, `visibility`, `owned`, `deduped`.

An attachment whose server status is not `ready` is not included in a turn. Source pinning uses only IDs returned by the source API and applies to the next request. Citation labels, tenant scope, page/range and verification state are never invented.

## Frozen test examples

The parser regression vectors cover a split CRLF `answer` record, one malformed record, and `done`. The container probe `scripts/demo18_chat_probe.py` records an authenticated terminal turn with source and answer events without logging tokens, prompts, sources, or model output.
