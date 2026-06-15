# TAX-ASSISTANT-AGENT — đào sâu thiết kế (agent #3: trợ lý thuế VN)

> Từ [research/AGENT-OPPORTUNITIES.md](research/AGENT-OPPORTUNITIES.md): Trợ lý thuế = **#3, VN-native MOAT cao** (ngoại không làm). **Chưa code.** **Mở rộng** cross-check của [MONEY-ENGINE-AP-TAX.md](MONEY-ENGINE-AP-TAX.md) use-case B sang quyết toán + BHXH + giải trình.

## 0. Agent làm gì
> Trợ lý **tuân thủ & quyết toán thuế VN**: đối chiếu hoá đơn ↔ tờ khai ↔ sổ, hỗ trợ quyết toán TNDN/GTGT/TNCN, bắt sai lệch → **draft kiến nghị/giải trình chờ duyệt**. KHÔNG tự nộp tờ khai, KHÔNG tự quyết xử lý thuế phức tạp.

## 1. Phạm vi (3 lớp, tăng dần judgment)
1. **Tra cứu & tuân thủ** (rủi ro thấp — đã mạnh): RAG có dẫn chứng trên TT/NĐ thuế (GTGT, TNDN, hoá đơn điện tử NĐ70, BHXH) → trả lời + trích dẫn điều khoản.
2. **Cross-check & bắt sai lệch** (rủi ro thấp-TB): hoá đơn đầu ra/vào ↔ tờ khai GTGT; doanh thu sổ ↔ tờ khai TNDN; → bắt **bỏ sót/sai thuế suất/lệch**; draft kiến nghị điều chỉnh.
3. **Hỗ trợ quyết toán & giải trình** (TB): soạn **nháp** bảng quyết toán + văn bản giải trình chênh lệch hoá đơn → người duyệt.

## 2. Luồng
```
[hoá đơn điện tử XML + tờ khai + sổ ERP]
 → [DETERMINISTIC] đối chiếu + tính chênh lệch (calc Decimal)
 → [DETERMINISTIC] bắt sai lệch theo RULE thuế VN (thuế suất, kỳ, MST)
 → [LLM-GỢI-Ý] giải thích + soạn nháp giải trình/kiến nghị (trích dẫn điều khoản TT/NĐ)
 → [DETERMINISTIC] verify-gate: số khớp hoá đơn/tờ khai/sổ + trích dẫn
 → [HITL] draft (kind="tax_adjustment"/"tax_explanation") chờ kế toán/đại lý thuế duyệt
```

## 3. VN-native MOAT (vì sao ngoại không làm)
Cần hiểu **schema hoá đơn điện tử VN (TT78) + mẫu tờ khai GTGT/TNDN/TNCN + quy tắc thuế VN + BHXH** — SAP/Oracle/MISA-cloud/AI ngoại không có. Gắn thẳng Tax&AP engine (dùng chung parser hoá đơn + map TK).

## 4. Tái dùng bravo
| Thành phần | ĐÃ CÓ | Cần thêm |
|---|---|---|
| Tra cứu chuẩn mực/luật thuế | ✅ RAG + citations (mạnh) | nạp corpus TT/NĐ thuế |
| Số không bịa | ✅ verify-gate | — |
| Draft chờ duyệt | ✅ draft_queue + maker-checker | UI review kiến nghị thuế |
| Parser hoá đơn XML | ⚠️ (Tax&AP engine đang xây) | dùng chung |
| Đối chiếu/rule thuế | ❌ | **parser tờ khai + rule thuế VN** |

## 5. Ranh giới — chỗ AI KHÔNG tự quyết
- **KHÔNG tự nộp tờ khai / tự quyết toán** — chỉ draft chờ người.
- **KHÔNG tự quyết xử lý thuế phức tạp** (ưu đãi, chuyển lỗ, giá chuyển nhượng — judgment cao → kế toán/đại lý thuế).
- LLM không sinh số thuế; số từ hoá đơn/tờ khai/calc; verify-gate chặn.
- Rủi ro pháp lý cao nếu sai → **HITL + audit-trail bắt buộc** (đúng moat của bravo).

## 6. ROI (pilot đo)
Số sai lệch hoá đơn-tờ khai bắt sớm · **tránh phạt thuế** · thời gian quyết toán/giải trình giảm · % kiến nghị duyệt-không-sửa. ⚠️ pilot, không số vendor.

## 7. Phụ thuộc & cảnh báo
- Hoá đơn điện tử (XML — dùng chung Tax&AP) · **mẫu tờ khai + rule thuế VN** (cần kế toán/đại lý thuế BRAVO) · API tra MST/NCC.
- **Điểm vào AN TOÀN NHẤT = lớp 1 (tra cứu luật thuế có dẫn chứng)** — rủi ro thấp, dùng đúng thế mạnh RAG, làm sớm; cross-check + quyết toán làm sau.
- ROI = kỳ vọng pilot; giữ HITL tuyệt đối (sai thuế = rủi ro pháp lý).
