# Chủ quyền dữ liệu & vì sao demo dùng cloud — làm rõ câu hỏi pháp lý

> Trả lời câu hỏi: *"Có luật về không chuyển thông tin doanh nghiệp ra nước ngoài, vậy vì sao MISA AI vẫn dùng provider model nước ngoài (cho dùng ChatGPT/Gemini...), và dự án hải quan (agent-ai) vẫn gửi dữ liệu tới model quốc tế như Cursor?"*
> Căn cứ: nghiên cứu pháp lý đã kiểm chứng từ **văn bản gốc** ([findings/E](research/findings/E-vietnam-legal.md), [findings/F §0-1](research/findings/F-reverification.md)). ⚠️ Số điều/mẫu cụ thể cần **luật sư BRAVO** đối chiếu bản công báo trước khi đưa vào tài liệu bán hàng.

---

## 1. Hiểu lầm cốt lõi: luật KHÔNG "cấm", mà đặt **nghĩa vụ tuân thủ**

Không có điều luật nào *cấm* gửi dữ liệu ra nước ngoài. Luật BVDLCN **91/2025/QH15** (hiệu lực **1/1/2026**, Điều 20) coi việc đưa dữ liệu ra nước ngoài là **"chuyển dữ liệu cá nhân xuyên biên giới"** → phát sinh **nghĩa vụ** (hồ sơ đánh giá tác động chuyển dữ liệu — CTIA, nộp Cục An ninh mạng A05 trong 60 ngày; phạt tới **3 tỷ đồng / 5% doanh thu** nếu vi phạm). Đây là **cơ chế đăng ký + chịu trách nhiệm**, không phải lệnh cấm. Có cơ sở pháp lý (đặc biệt **sự đồng ý** của chủ thể dữ liệu) + làm đúng hồ sơ ⇒ **được phép** chuyển.

Hai giới hạn quan trọng của phạm vi điều chỉnh:
- **Chỉ áp dụng cho "dữ liệu cá nhân" của công dân VN** — *không* phải mọi "thông tin doanh nghiệp". Phần lớn dữ liệu nghiệp vụ thuần (mã HS, số lượng, thông số sản phẩm, chỉ tiêu tổng hợp, nội dung cẩm nang) **không** là dữ liệu cá nhân được bảo vệ. Luật Dữ liệu **60/2024**: dữ liệu *thông thường* được tự do chuyển; chỉ "dữ liệu cốt lõi/quan trọng" bị siết (phạm vi hẹp).
- **Miễn trừ dữ liệu nhân viên của chính mình** (Khoản 6 Điều 20): tổ chức lưu dữ liệu cá nhân của **nhân viên mình** trên cloud (kể cả nước ngoài) được **miễn** CTIA. ⇒ Đòn bẩy on-prem **chỉ mạnh cho dữ liệu KHÁCH HÀNG/đối tác**, *không* dùng cho HR/lương nội bộ.

---

## 2. Vì sao MISA / dự án hải quan vẫn dùng model nước ngoài — mà không phạm luật

Vì con đường tuân thủ **tồn tại và hợp pháp**:

1. **Phần lớn dữ liệu gửi đi không phải "dữ liệu cá nhân được bảo vệ"** — câu hỏi nghiệp vụ, số liệu tổng hợp, tờ khai hải quan (HS code, số lượng, trị giá) phần lớn là dữ liệu thương mại, không phải PII công dân (dù MST cá nhân/tên người có thể là PII — vùng xám).
2. **Có sự đồng ý + cơ sở pháp lý:** MISA (cloud-only) chuyển nghĩa vụ thành **opt-in của khách** + hoàn tất hồ sơ CTIA/DPIA → chuyển xuyên biên giới trở nên hợp pháp. Đây là **chấp nhận gánh nặng giấy tờ + rủi ro**, không phải làm chui. *(Lưu ý: A05 báo <20% hồ sơ đạt chuẩn — nhiều bên đang ở vùng xám/chấp nhận rủi ro.)*
3. **Công cụ nội bộ chấp nhận rủi ro:** dự án hải quan (Atlas Builder) là công cụ **nội bộ của đại lý**, người vận hành đồng ý dùng; quy mô nhỏ; thường vận hành dưới dạng *chấp nhận rủi ro tuân thủ* hơn là đã hoàn tất CTIA chính thức. Phổ biến, không có nghĩa là đã chuẩn hóa pháp lý.

> Tóm lại: dùng model nước ngoài **là khả thi về mặt pháp lý** (với đồng ý + hồ sơ + phần lớn data không phải PII) và **phổ biến** (chấp nhận rủi ro). Cái mà các bên cloud-only **không tránh được** là **gánh nặng + rủi ro phạt** cho phần dữ liệu cá nhân khách hàng/đối tác *thật sự* được bảo vệ.

---

## 3. Định vị đúng cho BRAVO (đừng phóng đại)

On-prem/local **không** làm cloud "phạm luật với người khác". Nó **loại bỏ gánh nặng + rủi ro** (hồ sơ CTIA, rủi ro rò rỉ xuyên biên giới, phơi nhiễm phạt 3 tỷ/5%) cho **đúng phần dữ liệu được bảo vệ** (khách hàng/đối tác). Đó là điểm bán cho **phân khúc** coi trọng điều này (tài chính regulated, an ninh chặt, air-gapped) — **không phải tuyên bố "cloud là bất hợp pháp"**.

Quan trọng: thiết kế **hybrid** ([ADR-0003](adr/0003-hybrid-llm-strategy.md)) giúp BRAVO **vẫn dùng được cloud** (như MISA) khi khách opt-in cho dữ liệu không nhạy — chỉ khác là **local là sàn được đảm bảo**. Thông điệp đúng (đã kiểm chứng [findings/F §0](research/findings/F-reverification.md)):

> *"On-prem giữ dữ liệu **khách hàng & nghiệp vụ** trong nước → tránh nghĩa vụ & rủi ro phạt khi chuyển xuyên biên giới; vẫn cho phép cloud opt-in có kiểm soát cho dữ liệu không nhạy."* — **Không** quảng cáo đòn bẩy này cho HR/lương nội bộ (đã miễn trừ).

---

## 4. Vì sao **demo của BRAVO** dùng cloud (và vẫn nhất quán nguyên tắc)

Demo hiện tại chạy trên **cloud model** ([config.py](../app/config.py): `embedding_provider=openai_compatible`, `demo_allow_cloud_answers`) vì **máy demo yếu** và:
- **Corpus demo là dữ liệu KHÔNG nhạy** — cẩm nang BRAVO 10 + quy trình triển khai (tài liệu hướng dẫn, gần như công khai), **không có PII khách hàng**.
- **Dữ liệu tài chính trong demo là MOCK** (giả, gắn nhãn "DEMO") — không phải số liệu thật của doanh nghiệp nào.

⇒ Demo cloud **không vi phạm** gì (không có dữ liệu cá nhân được bảo vệ rời mạng). Đồng thời, **kiến trúc egress-classification + audit** ([ADR-0011](adr/0011-egress-classification-audit.md)) vẫn được xây trong demo để **trình diễn** rằng: ở production, dữ liệu gắn nhãn nhạy (kế toán/lương/HR) sẽ **fail-closed về local**, không bao giờ tự rời mạng. Đó chính là điểm bán "chủ quyền" được demo bằng cơ chế, không phải lời hứa.

**Lộ trình:** khi có GPU + LLM cục bộ (Qwen-2.5), chuyển đường chạy nhạy sang local; cloud chỉ còn opt-in cho dữ liệu whitelist. Sàn offline được đo bằng spike ([AGENTIC-SPIKE-WS0.md](AGENTIC-SPIKE-WS0.md)) + CI air-gapped khi triển khai production.

---

## 5. Việc cần luật sư BRAVO xác nhận (trước khi dùng làm điểm bán)
- Ranh giới chính xác miễn trừ Khoản 6 Điều 20 (có gồm lương/BHXH/đánh giá hiệu suất?).
- Số điều/mẫu CTIA/DPIA của **NĐ 356/2025** (bản công báo).
- Phạm vi "dữ liệu cốt lõi/quan trọng" của Luật Dữ liệu 60/2024 áp cho dữ liệu kế toán/khách hàng.
