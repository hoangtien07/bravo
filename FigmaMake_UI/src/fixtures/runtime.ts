export const FIXTURE_EPOCH = Date.UTC(2026, 5, 30, 2, 0, 0);

let sequence = 0;

export function fixtureNow(offsetMs = 0): string {
  return new Date(FIXTURE_EPOCH + offsetMs).toISOString();
}

export function fixtureId(kind: string): string {
  sequence += 1;
  return `fixture:${kind}:${String(sequence).padStart(4, "0")}`;
}

export function resetFixtureSequence(): void {
  sequence = 0;
}

export type MockStreamEvent = { id: string; event: string; atMs: number; payload?: unknown };

export function mockStreamSchedule(runId = "fixture:run:0001"): MockStreamEvent[] {
  const eventNames = [
    "id", "plan", "plan_update", "status", "step", "tool_call", "tool_result",
    "source", "attachments", "artifact", "draft", "answer", "ping", "done",
  ];
  return eventNames.map((event, index) => ({
    id: `${runId}:${String(index + 1).padStart(2, "0")}`,
    event,
    atMs: index * 160,
    payload: event === "answer" ? { delta: "[Nội dung minh họa]" } : undefined,
  }));
}

export function assertFixtureIdentifier(value: string): void {
  if (!value.startsWith("fixture:")) throw new Error("Fixture service rejected a non-fixture identifier");
}

export function installFixtureNetworkGuard(): () => void {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() => Promise.reject(new Error("Network disabled in fixture-only prototype"))) as typeof fetch;
  return () => { globalThis.fetch = originalFetch; };
}

