import React, { useEffect, useState } from "react";
import { Banner, DiagonalMotif, Button, Input, T } from "./shared";
import bravoLogo from "../imports/bravo-logo.png";

interface SignInProps {
  onSignIn: () => void;
}

export default function SignIn({ onSignIn }: SignInProps) {
  const scenario = new URLSearchParams(window.location.search).get("scenario")?.toUpperCase() ?? "AUTH-01";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(scenario === "AUTH-04" ? "Email hoặc mật khẩu mô phỏng không đúng. Kiểm tra lại hoặc dùng phương thức đăng nhập được cấp." : null);
  const [width, setWidth] = useState(window.innerWidth);
  const isMobile = width < 768;
  const ssoEnabled = scenario !== "AUTH-02";
  const passwordEnabled = scenario !== "AUTH-03";

  useEffect(() => {
    const update = () => setWidth(window.innerWidth);
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (scenario === "AUTH-04") { setError("Không thể đăng nhập bằng thông tin mô phỏng này. Không có yêu cầu nào được gửi đi."); return; }
    setLoading(true);
    setTimeout(() => { setLoading(false); onSignIn(); }, 900);
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: T.canvas, fontFamily: "inherit" }}>
      {/* Left panel */}
      {!isMobile && <div style={{ flex: "0 0 52%", background: T.white, display: "flex", flexDirection: "column", justifyContent: "center", padding: "64px 72px", borderRight: `1px solid ${T.border}`, position: "relative", overflow: "hidden" }}>
        {/* Background // motif — large, subtle */}
        <div style={{ position: "absolute", bottom: -40, right: -20, opacity: 0.06, pointerEvents: "none" }}>
          <DiagonalMotif size={320} color="#00A88D" />
        </div>

        <div style={{ maxWidth: 480 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <img src={bravoLogo} alt="BRAVO" style={{ height: 36, width: "auto", display: "block" }} />
            <span style={{ fontSize: 16, fontWeight: 600, color: "#1F2927", borderLeft: "1px solid #D7E1DE", paddingLeft: 12, marginLeft: 4 }}>Agent AI</span>
          </div>

          {/* Thesis */}
          <h1 style={{ fontSize: 28, lineHeight: "34px", fontWeight: 600, color: "#1F2927", margin: "0 0 16px 0" }}>
            Trợ lý nghiệp vụ<br />có bằng chứng
          </h1>
          <p style={{ fontSize: 14, lineHeight: "22px", color: "#56625F", margin: "0 0 40px 0", maxWidth: 380 }}>
            Hỗ trợ kiểm toán viên, kế toán trưởng và quản lý tài chính trong quy trình đóng kỳ kế toán — có bằng chứng, có phân quyền, có kiểm soát bản nháp.
          </p>

          {/* // motif as separator */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 32 }}>
            <DiagonalMotif size={20} color="#00A88D" />
            <span style={{ fontSize: 13, color: "#56625F", fontWeight: 500 }}>Financial Close Advisor</span>
          </div>

          {/* Feature list */}
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              "Kiểm tra mức độ sẵn sàng đóng kỳ",
              "Đối chiếu bằng chứng và điều kiện",
              "Kiểm soát bản nháp và phê duyệt",
              "Truy xuất nguồn gốc tài liệu",
            ].map(item => (
              <li key={item} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: "#56625F" }}>
                <span style={{ color: "#00A88D", fontWeight: 700, fontSize: 16 }}>✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>}

      {/* Right panel */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", padding: isMobile ? "28px 20px" : "48px 40px" }}>
        <div style={{ width: "100%", maxWidth: 360 }}>
          {isMobile && <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}><img src={bravoLogo} alt="BRAVO" style={{ height: 28 }} /><strong>Agent AI</strong></div>}
          <h2 style={{ fontSize: 20, lineHeight: "28px", fontWeight: 600, color: "#1F2927", margin: "0 0 8px 0" }}>Đăng nhập</h2>
          <p style={{ fontSize: 14, color: "#56625F", margin: "0 0 32px 0" }}>Đăng nhập vào môi trường BRAVO của bạn</p>

          <Banner variant="info"><strong>Xác thực mô phỏng.</strong> Màn hình này không gửi mật khẩu, không mở OIDC thật và không chứng minh quyền truy cập.</Banner>
          {scenario === "AUTH-06" && <Banner variant="warning"><strong>Phiên đã hết hạn.</strong> Đăng nhập lại để tiếp tục tới địa chỉ an toàn đã lưu.</Banner>}
          {scenario === "AUTH-08" && <Banner variant="warning"><strong>Đang ngoại tuyến.</strong> Đăng nhập mới không khả dụng; liên hệ hỗ trợ nội bộ.</Banner>}
          {error && <Banner variant="error"><strong>Đăng nhập không thành công.</strong> {error}</Banner>}

          {/* SSO primary */}
          {ssoEnabled && <>
          <Button
            variant="secondary"
            style={{ width: "100%", justifyContent: "center", marginBottom: 16, padding: "10px 16px" }}
            onClick={onSignIn}
            disabled={scenario === "AUTH-08"}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <rect x="1" y="1" width="6.5" height="6.5" rx="1" fill="#4285F4"/>
              <rect x="8.5" y="1" width="6.5" height="6.5" rx="1" fill="#34A853"/>
              <rect x="1" y="8.5" width="6.5" height="6.5" rx="1" fill="#FBBC05"/>
              <rect x="8.5" y="8.5" width="6.5" height="6.5" rx="1" fill="#EA4335"/>
            </svg>
            Đăng nhập bằng Google Workspace
          </Button>

          {/* Divider */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
            <div style={{ flex: 1, height: 1, background: "#D7E1DE" }} />
            <span style={{ fontSize: 12, color: "#56625F" }}>hoặc</span>
            <div style={{ flex: 1, height: 1, background: "#D7E1DE" }} />
          </div>
          </>}

          {passwordEnabled ? <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label htmlFor="email" style={{ fontSize: 13, fontWeight: 500, color: "#1F2927", display: "block", marginBottom: 6 }}>Email</label>
              <Input
                id="email"
                type="email"
                placeholder="ten@congty.com.vn"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
            <div>
              <label htmlFor="password" style={{ fontSize: 13, fontWeight: 500, color: "#1F2927", display: "block", marginBottom: 6 }}>Mật khẩu</label>
              <div style={{ position: "relative" }}>
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  style={{ paddingRight: 44 }}
                />
                <button type="button" onClick={() => setShowPassword(v => !v)} style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "#56625F", cursor: "pointer", padding: 2, fontSize: 13 }} aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}>
                  {showPassword ? "Ẩn" : "Hiện"}
                </button>
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button type="button" style={{ fontSize: 13, color: "#006B5D", background: "none", border: "none", cursor: "pointer", padding: 0 }}>Quên mật khẩu?</button>
            </div>
            <Button
              type="submit"
              variant="primary"
              style={{ width: "100%", justifyContent: "center", padding: "10px 16px", opacity: loading ? 0.7 : 1 }}
              disabled={loading}
            >
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
            </Button>
          </form> : <Banner variant="warning"><strong>Đăng nhập bằng mật khẩu đã tắt.</strong> Dùng SSO hoặc liên hệ quản trị viên.</Banner>}

          {/* Environment info */}
          <div style={{ marginTop: 32, padding: "12px 16px", background: "#fff", border: "1px solid #D7E1DE", borderRadius: 8 }}>
            <p style={{ fontSize: 12, color: "#56625F", margin: 0 }}>
              <span style={{ fontWeight: 500, color: "#1F2927" }}>Môi trường:</span> Chưa xác định
            </p>
            <p style={{ fontSize: 12, color: "#56625F", margin: "4px 0 0 0" }}>
              Liên hệ quản trị viên nếu bạn không có tài khoản.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
