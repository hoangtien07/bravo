/**
 * Centralized typed fixtures for Design QA mode.
 * These are illustration data only — not real financial information.
 * All components read from this file rather than embedding data inline.
 *
 * Label: DỮ LIỆU MINH HỌA — KHÔNG PHẢI DỮ LIỆU THỰC
 */

import type {
  PrerequisiteNode,
  EvidenceRef,
  DraftItem,
  KnowledgeDoc,
  EnvironmentScope,
  ConversationMessage,
  QAScenario,
} from "../state/types";

// ── Scope fixtures ────────────────────────────────────────────────────────

export const SCOPE_UNKNOWN: EnvironmentScope = {
  company:          { known: false },
  branch:           { known: false },
  accountingPeriod: { known: false },
  bravoVersion:     { known: false },
  environment:      { known: false },
};

export const SCOPE_ILLUSTRATION: EnvironmentScope = {
  company:          { known: true, value: "[Công ty minh họa]" },
  branch:           { known: true, value: "[Chi nhánh minh họa]" },
  accountingPeriod: { known: true, value: "[Kỳ minh họa]" },
  bravoVersion:     { known: true, value: "[Phiên bản minh họa]" },
  environment:      { known: true, value: "[Môi trường minh họa]" },
};

// ── Evidence fixtures ─────────────────────────────────────────────────────

export const EVIDENCE_ILLUSTRATION: EvidenceRef[] = [
  {
    id: "ev-1",
    claim: "Chứng từ gốc trong kỳ đã được hạch toán",
    evidenceClass: "inferred",
    sourceName: "[Nguồn chưa được liên kết]",
    locator: "[Chưa xác định phạm vi]",
    company: "[Công ty minh họa]",
    period: "[Kỳ minh họa]",
    environment: "[Môi trường minh họa]",
    bravoVersion: "[Phiên bản minh họa]",
    effectiveStatus: "unknown",
    freshness: "unknown",
  },
  {
    id: "ev-2",
    claim: "Số dư đầu kỳ khớp với kỳ trước",
    evidenceClass: "inferred",
    sourceName: "[Nguồn chưa được liên kết]",
    locator: "[Chưa xác định phạm vi]",
    company: "[Công ty minh họa]",
    period: "[Kỳ minh họa]",
    effectiveStatus: "unknown",
    freshness: "unknown",
  },
  {
    id: "ev-3",
    claim: "Đối chiếu công nợ phải thu",
    evidenceClass: "conflicting",
    sourceName: "[Nguồn chưa được liên kết]",
    locator: "[Chưa xác định phạm vi]",
    company: "[Công ty minh họa]",
    period: "[Kỳ minh họa]",
    conflictNote: "Có chênh lệch cần giải trình. Chi tiết phụ thuộc bằng chứng được cung cấp.",
    freshness: "unknown",
  },
  {
    id: "ev-4",
    claim: "Biên bản kiểm kê kho vật lý cuối kỳ",
    evidenceClass: "missing",
    sourceName: "[Chưa cung cấp]",
    period: "[Kỳ minh họa]",
    effectiveStatus: "unknown",
    freshness: "unknown",
  },
];

// ── Prerequisite fixtures ─────────────────────────────────────────────────


function makePrereqs(scenario: QAScenario): PrerequisiteNode[] {
  const base: PrerequisiteNode[] = [
    {
      id: "prereq-scope",
      step: 1,
      title: "Phạm vi và kỳ báo cáo",
      description: "Xác định công ty, chi nhánh, kỳ kế toán và phiên bản áp dụng.",
      prerequisiteIds: [],
      applicability: "applicable",
      status: "not_assessed",
      reason: "Phạm vi chưa được xác nhận.",
      evidenceRefs: [],
      missingEvidence: ["Xác nhận công ty, chi nhánh và kỳ kế toán áp dụng"],
      responsibleRole: "Quản trị viên",
    },
    {
      id: "prereq-source-docs",
      step: 2,
      title: "Chứng từ nguồn đã ghi nhận",
      description: "Tất cả chứng từ gốc trong kỳ đã được kiểm tra và ghi nhận đầy đủ.",
      prerequisiteIds: ["prereq-scope"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — phụ thuộc phạm vi kỳ.",
      evidenceRefs: [],
      missingEvidence: ["Danh sách chứng từ gốc trong kỳ", "Xác nhận trạng thái phê duyệt"],
      responsibleRole: "Kế toán viên",
    },
    {
      id: "prereq-subledgers",
      step: 3,
      title: "Đối chiếu sổ phụ",
      description: "Công nợ, tài sản cố định, tồn kho và các sổ phụ đã được đối chiếu với sổ cái chính.",
      prerequisiteIds: ["prereq-source-docs"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — phụ thuộc bước 2.",
      evidenceRefs: [],
      missingEvidence: ["Kết quả đối chiếu từng sổ phụ"],
      responsibleRole: "Kế toán tổng hợp",
    },
    {
      id: "prereq-period-processes",
      step: 4,
      title: "Nghiệp vụ định kỳ áp dụng",
      description: "Tính lương, khấu hao, phân bổ và các nghiệp vụ định kỳ đã hoàn thành.",
      prerequisiteIds: ["prereq-scope"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — cần xác định danh sách nghiệp vụ áp dụng cho kỳ.",
      evidenceRefs: [],
      missingEvidence: ["Danh sách nghiệp vụ định kỳ áp dụng", "Bằng chứng hoàn thành từng nghiệp vụ"],
      responsibleRole: "Kế toán tổng hợp",
    },
    {
      id: "prereq-period-end",
      step: 5,
      title: "Bút toán cuối kỳ",
      description: "Các bút toán điều chỉnh, dự phòng và kết chuyển cuối kỳ đã được lập và phê duyệt.",
      prerequisiteIds: ["prereq-subledgers", "prereq-period-processes"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — phụ thuộc bước 3 và 4.",
      evidenceRefs: [],
      missingEvidence: ["Danh sách bút toán cuối kỳ", "Bằng chứng phê duyệt"],
      responsibleRole: "Kế toán trưởng",
    },
    {
      id: "prereq-closing-controls",
      step: 6,
      title: "Kiểm soát đóng kỳ",
      description: "Các kiểm soát tự động và thủ công đã được thực hiện và xác nhận kết quả.",
      prerequisiteIds: ["prereq-period-end"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — phụ thuộc bước 5.",
      evidenceRefs: [],
      missingEvidence: ["Kết quả chạy kiểm soát tự động", "Xác nhận kiểm soát thủ công"],
      responsibleRole: "Kế toán trưởng",
    },
    {
      id: "prereq-mappings",
      step: 7,
      title: "Ánh xạ báo cáo và số dư đầu kỳ",
      description: "Ánh xạ tài khoản sang mẫu biểu và số dư đầu kỳ tiếp theo đã được kiểm tra.",
      prerequisiteIds: ["prereq-closing-controls"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — phụ thuộc bước 6.",
      evidenceRefs: [],
      missingEvidence: ["Ánh xạ tài khoản sang mẫu biểu", "Số dư đầu kỳ tiếp theo"],
      responsibleRole: "Kế toán tổng hợp",
    },
    {
      id: "prereq-reports",
      step: 8,
      title: "Báo cáo và soát xét chênh lệch",
      description: "Báo cáo tài chính đã được lập và soát xét chênh lệch so với kỳ trước.",
      prerequisiteIds: ["prereq-mappings"],
      applicability: "unknown",
      status: "not_assessed",
      reason: "Chưa đánh giá — phụ thuộc bước 7.",
      evidenceRefs: [],
      missingEvidence: ["Bộ báo cáo tài chính", "Biên bản soát xét chênh lệch"],
      responsibleRole: "Kế toán trưởng",
    },
  ];

  if (scenario === "default_unknown") return base;

  if (scenario === "partial_assessment") {
    return base.map(n => {
      if (n.id === "prereq-scope") return { ...n, status: "ready" as const, reason: "Phạm vi đã được xác nhận — minh họa.", evidenceRefs: ["ev-1"] };
      if (n.id === "prereq-source-docs") return { ...n, status: "in_progress" as const, reason: "Còn một số chứng từ chưa được phê duyệt — minh họa.", evidenceRefs: ["ev-1"], missingEvidence: ["Xác nhận phê duyệt chứng từ còn tồn đọng"] };
      if (n.id === "prereq-period-processes") return { ...n, status: "in_progress" as const, reason: "Phân bổ chi phí trả trước chưa hoàn tất — minh họa.", evidenceRefs: [], missingEvidence: ["Phê duyệt bảng phân bổ chi phí trả trước"] };
      return n;
    });
  }

  if (scenario === "conflict_blocking") {
    return base.map(n => {
      if (n.id === "prereq-scope") return { ...n, status: "ready" as const, reason: "Phạm vi đã được xác nhận — minh họa.", evidenceRefs: ["ev-1"] };
      if (n.id === "prereq-source-docs") return { ...n, status: "ready" as const, reason: "Chứng từ đã đầy đủ — minh họa.", evidenceRefs: ["ev-1", "ev-2"] };
      if (n.id === "prereq-subledgers") return { ...n, status: "conflict" as const, reason: "Có chênh lệch đối chiếu cần giải trình — minh họa.", evidenceRefs: ["ev-3"], nextSafeAction: "Yêu cầu giải trình chênh lệch trước khi tiếp tục." };
      if (n.id === "prereq-period-end") return { ...n, status: "missing_evidence" as const, reason: "Thiếu bằng chứng kiểm kê kho — minh họa.", evidenceRefs: [], missingEvidence: ["Biên bản kiểm kê kho cuối kỳ"] };
      if (["prereq-closing-controls","prereq-mappings","prereq-reports"].includes(n.id)) return { ...n, status: "blocked" as const, reason: "Bị chặn bởi xung đột ở bước 3 — minh họa." };
      return n;
    });
  }

  if (scenario === "all_ready") {
    return base.map(n => ({ ...n, status: "ready" as const, reason: "Đã hoàn thành — minh họa.", applicability: "applicable" as const, evidenceRefs: ["ev-1", "ev-2"] }));
  }

  return base;
}

export function getPrerequisites(scenario: QAScenario): PrerequisiteNode[] {
  return makePrereqs(scenario);
}

// ── Draft fixtures ────────────────────────────────────────────────────────

export const DRAFT_ILLUSTRATION: DraftItem[] = [
  {
    id: "draft-1",
    title: "Bút toán điều chỉnh dự phòng cuối kỳ — minh họa",
    purpose: "Bổ sung dự phòng theo chính sách nội bộ áp dụng cho kỳ báo cáo.",
    scope: "Tài khoản dự phòng — kỳ báo cáo [minh họa]",
    beforeState: "Số dư dự phòng: [Chưa xác định — cần bằng chứng]",
    afterState: "Số dư dự phòng: [Đề xuất — xem bảng tính đính kèm, chưa được xác nhận]",
    risk: "Số liệu dự phòng phụ thuộc vào danh sách công nợ cuối kỳ chưa được xác nhận cuối cùng.",
    missingChecks: [
      "Xác nhận danh sách công nợ quá hạn cuối kỳ",
      "Phê duyệt tỷ lệ dự phòng từ kế toán trưởng",
    ],
    status: "ready_for_review",
    requesterRole: "Kế toán viên",
    revision: 1,
    evidenceRefs: [],
    auditTrail: [
      { role: "Kế toán viên", event: "Tạo bản nháp đề xuất", timestampLabel: "[Ngày minh họa]", revision: 1 },
      { role: "Hệ thống", event: "Kiểm tra định dạng — không có lỗi cú pháp", timestampLabel: "[Ngày minh họa]", revision: 1 },
    ],
  },
  {
    id: "draft-2",
    title: "Kết chuyển doanh thu cuối kỳ — minh họa",
    purpose: "Bút toán kết chuyển định kỳ theo quy trình chuẩn.",
    scope: "Tài khoản doanh thu và lợi nhuận — kỳ báo cáo [minh họa]",
    beforeState: "[Số dư trước kết chuyển — cần bằng chứng đối chiếu]",
    afterState: "[Số dư sau kết chuyển — đề xuất, chưa xác nhận]",
    risk: "Doanh thu chưa được đối chiếu đầy đủ với hóa đơn xuất.",
    missingChecks: ["Đối chiếu doanh thu với hóa đơn xuất trong kỳ"],
    status: "validation_failed",
    requesterRole: "Kế toán tổng hợp",
    revision: 2,
    evidenceRefs: [],
    validationIssues: ["Phát hiện chênh lệch doanh thu chưa được đối chiếu — cần giải trình trước khi xem xét."],
    auditTrail: [
      { role: "Kế toán tổng hợp", event: "Tạo bản nháp đề xuất", timestampLabel: "[Ngày minh họa]", revision: 1 },
      { role: "Hệ thống", event: "Phát hiện vấn đề kiểm tra", timestampLabel: "[Ngày minh họa]", revision: 1, note: "Xem mục Vấn đề kiểm tra" },
      { role: "Kế toán tổng hợp", event: "Cập nhật và gửi lại", timestampLabel: "[Ngày minh họa]", revision: 2 },
      { role: "Hệ thống", event: "Kiểm tra thất bại — xem vấn đề", timestampLabel: "[Ngày minh họa]", revision: 2 },
    ],
  },
  {
    id: "draft-3",
    title: "Điều chỉnh phân bổ chi phí trả trước — minh họa",
    purpose: "Phân bổ định kỳ theo bảng theo dõi chi phí trả trước đã phê duyệt.",
    scope: "Chi phí trả trước — kỳ báo cáo [minh họa]",
    beforeState: "[Số dư chi phí chờ phân bổ — cần bằng chứng]",
    afterState: "[Số dư sau phân bổ — đề xuất]",
    risk: "Bảng theo dõi chi phí trả trước phụ thuộc kỳ trước, cần kiểm tra còn hiệu lực.",
    missingChecks: [],
    status: "approved",
    requesterRole: "Kế toán viên",
    reviewerRole: "Kế toán trưởng",
    revision: 1,
    evidenceRefs: ["ev-2"],
    auditTrail: [
      { role: "Kế toán viên", event: "Tạo bản nháp đề xuất", timestampLabel: "[Ngày minh họa]", revision: 1 },
      { role: "Hệ thống", event: "Kiểm tra định dạng — đạt", timestampLabel: "[Ngày minh họa]", revision: 1 },
      { role: "Kế toán trưởng", event: "Đã phê duyệt", timestampLabel: "[Ngày minh họa]", revision: 1, note: "Phê duyệt — chưa thực hiện trên hệ thống" },
    ],
  },
];

// ── Knowledge fixtures ────────────────────────────────────────────────────

export const KNOWLEDGE_ILLUSTRATION: KnowledgeDoc[] = [
  {
    id: "doc-1",
    name: "Quy trình đóng kỳ kế toán — phiên bản hiện hành",
    type: "Quy trình nội bộ",
    owner: "[Phòng chức năng]",
    bravoVersion: { known: false },
    effectiveDate: { known: false },
    approvalStatus: "approved",
    visibility: "Nội bộ — Kế toán",
    ingestionStatus: "completed",
    traceability: { known: true, value: "Toàn bộ tài liệu — [Phạm vi chưa xác định]" },
  },
  {
    id: "doc-2",
    name: "Thông tư 200/2014/TT-BTC — Chế độ kế toán doanh nghiệp",
    type: "Văn bản pháp lý",
    owner: "Bộ Tài chính",
    bravoVersion: { known: true, value: "Tất cả phiên bản" },
    effectiveDate: { known: true, value: "01/01/2015" },
    approvalStatus: "approved",
    visibility: "Công khai",
    ingestionStatus: "completed",
    traceability: { known: true, value: "Toàn văn bản" },
  },
  {
    id: "doc-3",
    name: "Hướng dẫn cấu hình kiểm soát đóng kỳ — phiên bản minh họa",
    type: "Hướng dẫn BRAVO",
    owner: "[BRAVO Software]",
    bravoVersion: { known: false },
    effectiveDate: { known: false },
    approvalStatus: "draft",
    visibility: "Kỹ thuật — Tư vấn",
    ingestionStatus: "in_progress",
    traceability: { known: false },
    conflictNote: "Có thể xung đột với phiên bản cũ còn lưu — cần kiểm tra.",
  },
  {
    id: "doc-4",
    name: "Biên bản kiểm kê kho cuối kỳ — kỳ hiện tại [minh họa]",
    type: "Bằng chứng kiểm toán",
    owner: "[Phòng kho]",
    bravoVersion: { known: false },
    effectiveDate: { known: false },
    approvalStatus: "not_available",
    visibility: "Nội bộ — Kế toán kho",
    ingestionStatus: "missing",
    traceability: { known: true, value: "Chưa cung cấp" },
  },
];

// ── Conversation fixtures ─────────────────────────────────────────────────

export const CONVERSATION_SCOPING: ConversationMessage[] = [
  {
    id: "msg-1",
    role: "assistant",
    content: "",
    answer: {
      understoodOutcome: "Bravo Agent AI chưa xác định được phạm vi công việc cụ thể.",
      applicablePrerequisites: [],
      nextAction: "Để hỗ trợ chính xác hơn, anh/chị vui lòng cho biết: phạm vi công ty và kỳ kế toán đang làm việc là gì?",
      uncertainty: ["Chưa có phạm vi — mọi đánh giá điều kiện phụ thuộc thông tin này."],
      clarification: "Anh/chị đang làm việc cho kỳ kế toán nào và công ty nào?",
      evidenceRefs: [],
    },
    evidenceRefs: [],
    timestamp: "[Thời gian minh họa]",
  },
];

export const CONVERSATION_PARTIAL: ConversationMessage[] = [
  {
    id: "msg-u-1",
    role: "user",
    content: "Kiểm tra mức độ sẵn sàng đóng kỳ kế toán",
    evidenceRefs: [],
    timestamp: "[Thời gian minh họa]",
  },
  {
    id: "msg-a-1",
    role: "assistant",
    content: "",
    answer: {
      understoodOutcome: "Kiểm tra mức độ sẵn sàng đóng kỳ kế toán — phạm vi công ty và kỳ chưa được xác nhận.",
      applicablePrerequisites: [
        {
          heading: "Chứng từ nguồn",
          body: "Cần xác nhận tất cả chứng từ gốc đã được ghi nhận và phê duyệt.",
          evidenceRefs: ["ev-1"],
        },
        {
          heading: "Đối chiếu sổ phụ",
          body: "Chưa có kết quả đối chiếu — cần bằng chứng từ các sổ phụ liên quan.",
          evidenceRefs: [],
        },
      ],
      nextAction: "Cung cấp phạm vi công ty và kỳ kế toán cụ thể để có thể đánh giá điều kiện đóng kỳ.",
      uncertainty: [
        "Phạm vi công ty và kỳ kế toán chưa được xác nhận.",
        "Chưa đủ bằng chứng để xác nhận kết luận về trạng thái sẵn sàng.",
      ],
      clarification: "Anh/chị đang kiểm tra cho kỳ kế toán và công ty nào?",
      evidenceRefs: ["ev-1"],
    },
    evidenceRefs: ["ev-1"],
    timestamp: "[Thời gian minh họa]",
  },
];
