export type ApiFailureKind = "unauthorized" | "denied" | "unavailable" | "conflict" | "invalid" | "server" | "network";

export class ApiError extends Error {
  readonly name = "ApiError";

  constructor(
    readonly kind: ApiFailureKind,
    readonly status: number | null,
    message: string,
    readonly detail?: unknown,
  ) {
    super(message);
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError;
}

export type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export type HttpClientOptions = {
  fetchImpl?: FetchLike;
  getToken?: () => string | null;
};

export const CANDIDATE_TOKEN_KEY = "bravo_v2_candidate_token";

export function candidateToken(): string | null {
  return typeof window === "undefined" ? null : window.sessionStorage.getItem(CANDIDATE_TOKEN_KEY);
}

function failureKind(status: number): ApiFailureKind {
  if (status === 401) return "unauthorized";
  if (status === 403) return "denied";
  if (status === 404) return "unavailable";
  if (status === 409) return "conflict";
  if (status === 422) return "invalid";
  return "server";
}

async function responseDetail(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return undefined;
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function errorMessage(status: number, detail: unknown): string {
  if (typeof detail === "object" && detail !== null && "detail" in detail) {
    const message = (detail as { detail?: unknown }).detail;
    if (typeof message === "string" && message.trim()) return message;
  }
  return `Yêu cầu không thành công (${status}).`;
}

export type HttpClient = {
  requestJson<T>(path: string, init: RequestInit, decode: (value: unknown) => T): Promise<T>;
};

export function createHttpClient(options: HttpClientOptions = {}): HttpClient {
  const fetchImpl = options.fetchImpl ?? globalThis.fetch.bind(globalThis);
  const getToken = options.getToken ?? candidateToken;

  return {
    async requestJson<T>(path: string, init: RequestInit, decode: (value: unknown) => T): Promise<T> {
      const token = getToken();
      const headers = new Headers(init.headers);
      headers.set("accept", "application/json");
      if (init.body !== undefined && !headers.has("content-type")) headers.set("content-type", "application/json");
      if (token) headers.set("authorization", `Bearer ${token}`);

      let response: Response;
      try {
        response = await fetchImpl(path, { ...init, headers });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Không thể kết nối dịch vụ.";
        throw new ApiError("network", null, message, error);
      }

      const detail = await responseDetail(response);
      if (!response.ok) throw new ApiError(failureKind(response.status), response.status, errorMessage(response.status, detail), detail);
      return decode(detail);
    },
  };
}
