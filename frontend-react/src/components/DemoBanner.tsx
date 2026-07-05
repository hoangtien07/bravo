import { FlaskConical } from "lucide-react";

/**
 * Nhãn cảnh báo cho các màn chạy trên DỮ LIỆU MOCK (Anomaly/Tax/Knowledge Graph).
 * Điều kiện Accepted của ADR-0016 + yêu cầu Hội đồng (COUNCIL-REVIEW-2026-07): tuyệt đối
 * không để số mock đứng lẫn số thật mà không dán nhãn. Đóng băng 🧊 tới L3 + ≥1 khách thật.
 */
export function DemoBanner({ note }: { note?: string }) {
  return (
    <div
      role="note"
      className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning"
    >
      <FlaskConical className="h-4 w-4 shrink-0 mt-0.5" />
      <div>
        <b>DEMO — dữ liệu mock.</b> Màn hình này chạy trên số liệu giả để minh hoạ luồng, {" "}
        <u>chưa nối dữ liệu thật</u>. Không dùng cho quyết định nghiệp vụ.
        {note ? <> {note}</> : null}
      </div>
    </div>
  );
}
