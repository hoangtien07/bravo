import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the network seams so the store logic runs in isolation.
vi.mock("@/api/sse", () => ({
  streamChat: vi.fn(async (_cid: string, _q: string, onEvent: (e: any) => void) => {
    onEvent({ type: "done", grounded: true });
  }),
}));
vi.mock("@/api/workspace", () => ({
  uploadAttachment: vi.fn(async (file: File) => ({
    id: "att-" + file.name,
    filename: file.name,
    mime_type: file.type,
    size_bytes: 1,
    kind: file.type.startsWith("image/") ? "image" : "text",
    status: "ready",
    token_count: 0,
    error: null,
  })),
  deleteAttachment: vi.fn(async () => {}),
  getAttachment: vi.fn(async () => ({ status: "ready" })),
}));

import { useChat } from "./chat";
import { streamChat } from "@/api/sse";

beforeEach(() => {
  // jsdom lacks object-URL APIs used for image previews.
  (globalThis.URL as any).createObjectURL = vi.fn(() => "blob:x");
  (globalThis.URL as any).revokeObjectURL = vi.fn();
  useChat.setState({ conversationId: null, messages: [], sending: false, abort: null, staged: [] });
  (streamChat as any).mockClear();
});

describe("chat store — P0a attachment fail-loud", () => {
  it("first-turn attachment id survives the newConversation() wipe (RC-FE2)", async () => {
    const img = new File([new Uint8Array([1])], "a.png", { type: "image/png" });
    await useChat.getState().attach([img]);
    expect(useChat.getState().staged[0].status).toBe("ready");

    // conversationId is null here -> send() calls newConversation() which wipes staged:[].
    await useChat.getState().send("ảnh này là gì?");

    const call = (streamChat as any).mock.calls[0];
    expect(call).toBeTruthy();
    const attachmentIds = call[4]; // (cid, question, onEvent, signal, attachmentIds)
    expect(attachmentIds).toContain("att-a.png"); // NOT dropped by the wipe
  });

  it("send() only forwards ready attachments (defensive filter)", async () => {
    const img = new File([new Uint8Array([1])], "b.png", { type: "image/png" });
    await useChat.getState().attach([img]);
    // Force a non-ready straggler into staged.
    useChat.setState((s) => ({
      staged: [...s.staged, { localId: "x", name: "big.pdf", kind: "text", status: "pending" }],
    }));
    await useChat.getState().send("câu hỏi");
    const attachmentIds = (streamChat as any).mock.calls[0][4];
    expect(attachmentIds).toEqual(["att-b.png"]); // pending one excluded, ready one kept
  });
});
