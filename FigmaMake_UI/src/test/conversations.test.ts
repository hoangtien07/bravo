import { afterEach, describe, expect, it, vi } from "vitest";
import { conversationsApi } from "../api/conversations";
import { CANDIDATE_TOKEN_KEY } from "../api/http";

function response(body: unknown, status = 200): Response { return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } }); }

describe("Conversation API boundary", () => {
  afterEach(() => { sessionStorage.clear(); vi.restoreAllMocks(); });

  it("decodes only the owner-scoped conversation list contract", async () => {
    sessionStorage.setItem(CANDIDATE_TOKEN_KEY, "candidate-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response([{ id: "c1", title: "Một hội thoại", last_message_at: null, created_at: "2026-08-03T00:00:00Z" }])));
    await expect(conversationsApi.list()).resolves.toEqual([{ id: "c1", title: "Một hội thoại", lastMessageAt: null, createdAt: "2026-08-03T00:00:00Z" }]);
  });

  it("parses split SSE records and isolates malformed records", async () => {
    sessionStorage.setItem(CANDIDATE_TOKEN_KEY, "candidate-token");
    const stream = new ReadableStream<Uint8Array>({ start(controller) { const encoder = new TextEncoder(); controller.enqueue(encoder.encode('data: {"type":"answer","delta":"xin"}\r\n\r\ndata: malformed\n\n')); controller.enqueue(encoder.encode('data: {"type":"done"}\n\n')); controller.close(); } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(stream, { status: 200, headers: { "content-type": "text/event-stream" } })));
    const events: string[] = [];
    await conversationsApi.stream("00000000-0000-0000-0000-000000000001", "x", event => events.push(event.type), new AbortController().signal);
    expect(events).toEqual(["answer", "error", "done"]);
  });

  it("rejects fixture identifiers before a live request", async () => {
    sessionStorage.setItem(CANDIDATE_TOKEN_KEY, "candidate-token");
    const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock);
    await expect(conversationsApi.get("fixture:conversation-1")).rejects.toMatchObject({ kind: "invalid" });
    await expect(conversationsApi.stream("fixture:conversation-1", "x", () => undefined, new AbortController().signal)).rejects.toMatchObject({ kind: "invalid" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("does not prefetch a protected conversation without a session", async () => {
    const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock);
    await expect(conversationsApi.list()).rejects.toMatchObject({ kind: "unauthorized" });
    await expect(conversationsApi.stream("00000000-0000-0000-0000-000000000001", "x", () => undefined, new AbortController().signal)).rejects.toMatchObject({ kind: "unauthorized" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("makes an incomplete SSE terminal visibly recoverable", async () => {
    sessionStorage.setItem(CANDIDATE_TOKEN_KEY, "candidate-token");
    const stream = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new TextEncoder().encode('data: {"type":"answer","delta":"partial"}\n\n')); controller.close(); } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(stream, { status: 200, headers: { "content-type": "text/event-stream" } })));
    const events: string[] = [];
    await conversationsApi.stream("00000000-0000-0000-0000-000000000001", "x", event => events.push(event.type), new AbortController().signal);
    expect(events).toEqual(["answer", "error"]);
  });
});
