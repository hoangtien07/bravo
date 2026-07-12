import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Keep the render offline.
vi.mock("@/api/client", () => ({
  api: vi.fn(async () => ({})),
  authHeaders: () => ({}),
}));
vi.mock("@/api/workspace", () => ({
  listSources: vi.fn(async () => []),
  uploadAttachment: vi.fn(),
  deleteAttachment: vi.fn(),
  getAttachment: vi.fn(),
}));

import { useChat } from "@/store/chat";
import { AuiChatView } from "./AuiChatView";

beforeEach(() => {
  (Element.prototype as any).scrollTo = vi.fn();
  (globalThis.URL as any).createObjectURL = vi.fn(() => "blob:x");
  useChat.setState({
    conversationId: "c1",
    sending: false,
    staged: [],
    pinnedSources: [],
    messages: [
      { role: "user", content: "Câu hỏi kiểm thử", id: "u1" },
      { role: "assistant", content: "Trả lời có nội dung xác thực.", id: "a1", grounded: true, citations: [] },
    ],
  });
});

describe("AuiChatView — assistant-ui shell over the external store", () => {
  it("renders each message through MessageBubble via the ExternalStoreRuntime + ThreadPrimitive", async () => {
    render(
      <MemoryRouter initialEntries={["/c/c1"]}>
        <Routes>
          <Route path="/c/:id" element={<AuiChatView />} />
        </Routes>
      </MemoryRouter>,
    );
    // User question + (markdown-rendered) assistant answer appear -> converter + runtime +
    // ThreadPrimitive.Messages + BubbleFromMeta chain works end-to-end.
    expect(await screen.findByText(/Câu hỏi kiểm thử/)).toBeTruthy();
    expect(await screen.findByText(/nội dung xác thực/)).toBeTruthy();
    // The grounded badge from the REUSED MessageBubble domain renderer is present.
    expect(await screen.findByText(/đã kiểm chứng/)).toBeTruthy();
  });
});
