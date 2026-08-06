export type CaseFamily =
  | "AUTH" | "CHAT" | "HIST" | "SSE" | "CLOSE" | "DRAFT" | "KNOW"
  | "WORK" | "ADMIN" | "MONEY" | "ANOM" | "TAX" | "KGRAPH" | "SHARE" | "ROUTE";

export type ReviewCase = {
  id: string;
  family: CaseFamily;
  title: string;
  route: string;
  expectedBoundary: string;
};

const FAMILY_CONFIG: Record<CaseFamily, { count: number; route: string; label: string }> = {
  AUTH: { count: 8, route: "/login", label: "Đăng nhập và phiên" },
  CHAT: { count: 30, route: "/c/fixture:review", label: "Hội thoại" },
  HIST: { count: 10, route: "/conversations", label: "Lịch sử hội thoại" },
  SSE: { count: 18, route: "/c/fixture:stream", label: "Luồng sự kiện mô phỏng" },
  CLOSE: { count: 13, route: "/financial-close", label: "Đóng kỳ tài chính" },
  WORK: { count: 3, route: "/accounting-work", label: "Công việc AI — ba case" },
  DRAFT: { count: 18, route: "/approvals", label: "Bản nháp và phê duyệt" },
  KNOW: { count: 15, route: "/knowledge", label: "Kho tri thức" },
  ADMIN: { count: 12, route: "/admin", label: "Quản trị" },
  MONEY: { count: 10, route: "/tools/money-engine", label: "Money Engine" },
  ANOM: { count: 8, route: "/tools/anomaly", label: "Bất thường" },
  TAX: { count: 8, route: "/tools/tax", label: "Thuế" },
  KGRAPH: { count: 10, route: "/tools/knowledge-graph", label: "Knowledge Graph" },
  SHARE: { count: 6, route: "/shared/fixture:review", label: "Chia sẻ chỉ đọc" },
  ROUTE: { count: 5, route: "/khong-ton-tai", label: "Điều hướng an toàn" },
};

const boundaries: Partial<Record<CaseFamily, string>> = {
  AUTH: "Xác thực chỉ được mô phỏng; không gửi mật khẩu hoặc mở OIDC thật.",
  SSE: "Lịch biểu sự kiện xác định; không mở EventSource hoặc kết nối backend.",
  DRAFT: "Phê duyệt khác xuất, thực hiện và xác minh.",
  CLOSE: "Mức sẵn sàng chỉ là dữ liệu minh họa có bằng chứng.",
  WORK: "Bank, Voucher và Period Close dùng chung AccountingCase; UI không tự tính verdict hoặc thực thi BRAVO ERP.",
  SHARE: "Bề mặt chỉ đọc không dựng thao tác riêng tư.",
};

export const REVIEW_CASES: ReviewCase[] = Object.entries(FAMILY_CONFIG).flatMap(([family, config]) =>
  Array.from({ length: config.count }, (_, index) => {
    const id = `${family}-${String(index + 1).padStart(2, "0")}`;
    return {
      id,
      family: family as CaseFamily,
      title: `${config.label} · trường hợp ${index + 1}`,
      route: config.route,
      expectedBoundary: boundaries[family as CaseFamily] ?? "Dữ liệu minh họa, trạng thái và quyền không thay thế kiểm soát backend.",
    };
  }),
);

export const CASE_BY_ID = new Map(REVIEW_CASES.map(reviewCase => [reviewCase.id, reviewCase]));

export function reviewUrl(reviewCase: ReviewCase): string {
  const delimiter = reviewCase.route.includes("?") ? "&" : "?";
  return `${reviewCase.route}${delimiter}qa=1&scenario=${reviewCase.id}&state=ready&theme=light`;
}
