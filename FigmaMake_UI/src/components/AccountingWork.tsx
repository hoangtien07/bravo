import { useQA } from "../context/QAContext";
import { AccountingWorkInbox } from "../accounting-work/CaseScreens";
import { Banner, T } from "./shared";

function QaAccountingWork() {
  return <section style={{ flex: 1, overflow: "auto", padding: "clamp(18px, 3vw, 32px)", background: T.canvas }}>
    <div style={{ maxWidth: 880, margin: "0 auto", background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 24 }}>
      <p style={{ color: T.interactive, fontSize: 12, fontWeight: 700, letterSpacing: ".06em" }}>DESIGN QA · FIXTURE ONLY</p>
      <h1 style={{ color: T.strong, margin: "6px 0" }}>Công việc AI</h1>
      <Banner variant="warning"><strong>Chế độ QA.</strong> Route này không gọi AccountingCase API và không thể mở lẫn fixture với dữ liệu live.</Banner>
      <p style={{ color: T.secondary }}>Thoát `?qa=1` để dùng inbox được bảo vệ và chỉ nhận dữ liệu đã được máy chủ cho phép.</p>
    </div>
  </section>;
}

export default function AccountingWork() {
  const { qa } = useQA();
  return qa.enabled ? <QaAccountingWork /> : <AccountingWorkInbox />;
}
