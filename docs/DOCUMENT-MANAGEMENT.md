# DOCUMENT-MANAGEMENT — Quản lý tài liệu & phân vùng khi scale

Trả lời câu hỏi: *khi corpus lớn dần và người dùng upload nhiều (nhiều end-user), quản lý tài
liệu thế nào? Có cần chia workspace kiểu "fusion lab" của agent-ai không, hay có cách tốt hơn?*

---

## 0. TL;DR (khuyến nghị)

1. **KHÔNG copy mô hình thư mục-theo-workspace của agent-ai.** agent-ai không thật sự có "fusion
   lab"; nó cô lập dữ liệu bằng **quy ước thư mục theo skill/khách hàng** — và **chính hội đồng
   của họ đánh dấu đó là rủi ro P1** (path traversal thoát khỏi lô/workspace,
   `agent-ai/docs/COUNCIL_DEMO_ASSESSMENT.md`). Cô lập bằng path **không đủ an toàn khi nhiều
   end-user**. Đó là điểm yếu nhất của họ, không phải điểm nên học.
2. **bravo ĐÃ có mô hình tốt hơn: 1 index pgvector dùng chung + RLS lọc ở tầng SQL.** Đây đúng
   là pattern chuẩn của các hệ enterprise search xuất sắc (Glean, Vectara, Elastic, Qdrant
   single-collection). Giữ nó — đừng đổi sang folder-per-workspace.
3. **Việc cần làm khi scale không phải "chia workspace vật lý", mà là 4 thứ:** (a) chuyển lưu file
   upload sang **object storage** (không để local disk), (b) thêm **một chiều "collection" trong
   metadata** để nhóm theo miền tri thức/khách hàng (vẫn 1 index + RLS), (c) **ingest bất đồng bộ
   + dedup theo content-hash + versioning**, (d) **hạn mức + vòng đời** (quota/retention/purge).
4. **Chỉ tách collection/namespace VẬT LÝ khi trở thành multi-CUSTOMER SaaS** (cần cô lập cứng
   giữa các công ty khách). Cho on-prem một tổ chức nhiều phòng ban → RLS logic là đủ và tốt hơn.

---

## 1. Bài học từ agent-ai (đã khảo sát repo thật)

| Khía cạnh | agent-ai (Atlas Builder) | Ý nghĩa cho bravo |
|---|---|---|
| "fusion lab" | **Không tồn tại**. "workspace" = thư mục bundle công cụ; đơn vị việc = "lô" | Không có gì để copy nguyên |
| Phân vùng tri thức | Theo **skill/khách hàng**, ranh giới cứng (cấm dùng chéo master) | ✅ Học: mỗi miền/khách một **namespace tri thức rõ ràng, cấm rò chéo** |
| Cô lập dữ liệu | **Bằng thư mục + đặt tên file**, KHÔNG RLS/DB | ❌ Council đánh P1 path-traversal → **không dùng cho nhiều user**. bravo dùng RLS-in-SQL |
| 3 loại dữ liệu tách bạch | tri thức bất biến (`experiences/`) · lookup runtime (`dictionary/`) · dữ liệu người dùng theo lô (`Inputs/Output`) | ✅ Học: **tách 3 loại** (xem §2) |
| Vector store | **Không có** (tra cứu CSV theo khóa) | bravo đã có pgvector — lợi thế |
| Versioning / dedup / queue | **Không có**; council khuyên chuyển cache sang **hash nội dung** | ✅ bravo nên làm dedup content-hash + versioning ngay |
| "Experience-as-skill" + "learned index" (`*_da_khai_index.csv`) | **Có** — kết quả xử lý trước thành từ điển cho lần sau | ✅ Pattern đáng học — nhưng gắn với **workspace/tenant id**, không phải file trong thư mục |

Kết: agent-ai mạnh ở **phân tách tri thức theo nghiệp vụ** và **tái dùng kết quả đã xử lý**; yếu ở
**cô lập (chỉ path) và vòng đời dữ liệu**. Lấy cái mạnh, tránh cái yếu.

---

## 2. Ba loại dữ liệu — tách bạch rõ (nguyên tắc nền)

bravo cũng có đúng 3 loại; quản lý mỗi loại KHÁC nhau (đã áp một phần, xem [DEPLOY-GCP.md §3](DEPLOY-GCP.md)):

| Loại | Bản chất | Lưu ở đâu (nay) | Khi scale nên chuyển |
|---|---|---|---|
| **Corpus tri thức** (bất biến) | Cẩm nang, quy trình, chính sách | `file_system/` versioned + bind-mount | Git LFS/GCS nếu >vài trăm MB |
| **Tài liệu người dùng upload** (mutable, nhiều) | PDF/DOCX/hoá đơn end-user nạp runtime | `data/uploads/` (named volume) | **Object storage GCS/S3/MinIO** (bắt buộc khi nhiều user/replica) |
| **Dữ liệu sống** (nháp/audit/hội thoại/**vector**) | Postgres + pgvector | volume `pgdata` | Cloud SQL / cụm Postgres partition |

Metadata + embedding của CẢ corpus lẫn upload đều vào **cùng bảng `chunks`** (1 index) — file gốc
thì tách kho như trên. Đây là chỗ nhiều người nhầm: *file gốc* tách kho, *chỉ mục truy hồi* dùng chung.

---

## 3. "Chia workspace" — chọn logic hay vật lý?

Có hai cách phân vùng tài liệu; đừng lẫn:

### 3a. Phân vùng LOGIC — 1 index chung + filter (★ bravo đang dùng, nên giữ)
Một bảng `chunks`, một HNSW index, lọc quyền bằng cột `department_ids` (GIN index, predicate `&&`
pushdown trong SQL — `app/security/rls.py::chunk_scope_filter`). Empty = global.

- **Ai dùng mô hình này:** Glean, Vectara, Elastic ESRE, Qdrant (khuyến nghị single-collection +
  payload filter cho đa số case), Pinecone (metadata filter). Đây là **mặc định enterprise**.
- **Ưu:** một chỗ để bảo mật (RLS), tìm kiếm xuyên miền cho admin, vận hành đơn giản, xoá/lọc theo
  metadata dễ. Mở rộng tới hàng triệu chunk nếu index đúng.
- **Nhược:** ở quy mô RẤT lớn, một index có thể "noisy neighbor"; độ chọn lọc của filter quan trọng.

**Nâng cấp đề xuất (rẻ, không phá kiến trúc):** thêm **một chiều `collection` (workspace)** vào
metadata chunk — bên cạnh `department_ids`. Ví dụ `collection = "cam_nang" | "chinh_sach_ke_toan" |
"khach_hang_ABC"`. Cho phép:
- Nhóm/lọc theo **miền tri thức** độc lập với phòng ban (một phòng có thể thấy nhiều collection).
- Người dùng chọn "hỏi trong collection nào" (thu hẹp nhiễu khi corpus lớn).
- Xoá/re-index/gán quyền theo collection.

Vẫn **1 index + filter** — chỉ thêm 1 cột + 1 GIN index. Đây là "workspace" đúng nghĩa cho bravo,
không phải folder.

### 3b. Phân vùng VẬT LÝ — collection/namespace riêng mỗi tenant
Mỗi workspace = một collection Qdrant / namespace Pinecone / bảng-partition pgvector riêng.

- **Chỉ nên khi:** multi-CUSTOMER SaaS — nhiều công ty khách, cần **cô lập cứng** (rò một dòng sang
  khách khác là sự cố hợp đồng), cần **xoá/scale/backup theo từng khách**, hoặc số vector mỗi tenant
  quá lớn.
- **Cái giá:** nhiều index để vận hành, tìm kiếm xuyên tenant khó, một mô hình bảo mật nữa phải giữ.
- **Với bravo on-prem một tổ chức:** **KHÔNG cần** — RLS logic vừa đủ vừa an toàn hơn folder.

> Quy tắc chọn: **< vài chục nghìn "workspace" hoặc cùng một tổ chức → logic (3a). Cần cô lập cứng
> giữa pháp nhân khách hàng → vật lý (3b).** Qdrant/Pinecone/Weaviate đều khuyến nghị đúng vậy.

---

## 4. Lưu trữ file upload khi NHIỀU end-user (quan trọng nhất)

`data/uploads/` trên **local disk** là nút thắt thật khi nhiều người dùng:
- Không chia sẻ được giữa nhiều replica api (scale ngang) → file "mất tích" tuỳ replica.
- Đầy đĩa VM; backup/khôi phục nặng; không có lifecycle.

**Khuyến nghị:** chuyển sang **object storage** (GCS / S3 / **MinIO** nếu on-prem air-gap):
- Ghi file gốc lên bucket theo khoá `{workspace}/{source_id}/{filename}`.
- `routes_sources.py` đổi `write_bytes`/`_locate_source_file` sang SDK object-store (một seam nhỏ).
- MinIO chạy trong compose = giữ chủ quyền/air-gap; API tương thích S3.
- Bật versioning + lifecycle (retention) ở bucket.

Corpus `file_system/` cũng có thể để bucket read-only khi phình lớn (hoặc Git LFS nếu vẫn muốn
đi cùng git).

---

## 5. Ingest & vòng đời khi tài liệu lớn dần

bravo đã có nền tốt (`app/ingestion/pipeline.py` idempotent re-index; `app/worker.py` arq queue).
Bổ sung khi scale:

- **Bất đồng bộ mặc định:** upload → tạo `Source(status=pending)` → **enqueue `ingest_task`** (đã
  có) thay vì ingest đồng bộ trong request (hiện `routes_sources` ingest sync — đổi sang enqueue khi
  volume lớn). Trả về ngay, cập nhật trạng thái sau.
- **Dedup theo content-hash:** hash SHA-256 nội dung file; nếu đã có Source cùng hash trong cùng
  collection → bỏ qua/parse lại (đúng bài học council agent-ai: hash **nội dung**, không phải path).
- **Incremental re-index:** chỉ re-embed source thay đổi (đã idempotent xoá-chunk-cũ; thêm so hash
  để bỏ qua source không đổi).
- **Versioning tài liệu:** giữ `version`/`effective_date` trên Source để trả lời "theo bản nào" và
  không trộn quy định cũ/mới (quan trọng với chính sách kế toán TT99 vs TT200).
- **Quota + retention:** hạn mức dung lượng/số file theo user/phòng ban; soft-delete + **purge
  chunk khỏi index** khi xoá (đừng để vector "mồ côi").
- **Trạng thái minh bạch:** trang `/documents` hiển thị pending/ready/failed + lý do (đã có khung).

---

## 6. Trần mở rộng của pgvector (khi thật sự lớn)

Một bảng `chunks` với HNSW phục vụ tốt tới ~vài triệu vector. Khi vượt:
- **Partition Postgres theo `collection`/tenant** (declarative partitioning) + **HNSW từng partition**
  → filter theo collection thành partition-pruning (nhanh hơn GIN filter trên bảng khổng lồ).
- Hoặc tách sang **Qdrant/Milvus** nếu cần sharding/scale chuyên dụng — nhưng mất RLS-in-SQL, phải
  tự dựng lại filter bảo mật ở tầng vector store (cân nhắc kỹ: đây là đánh đổi mất thế mạnh lớn nhất
  của bravo). Ưu tiên ở lại Postgres partition trước.

---

## 7. Lộ trình đề xuất (theo mức độ cần)

| Giai đoạn | Làm gì | Khi nào |
|---|---|---|
| **Ngay (rẻ)** | Giữ RLS 1-index. Thêm cột `collection` + GIN index + UI chọn collection | Khi có >1 miền tri thức hoặc corpus bắt đầu nhiễu |
| **Khi nhiều user upload** | Chuyển `data/uploads` → **MinIO/GCS**; ingest **enqueue** + **dedup content-hash** + quota | Khi upload runtime tăng / chạy >1 replica |
| **Khi nhiều dữ liệu** | Versioning tài liệu; purge-on-delete; incremental re-index | Khi corpus/upload lớn, có cập nhật thường xuyên |
| **Khi rất lớn** | Partition pgvector theo collection + HNSW/partition | Khi >vài triệu chunk hoặc latency tăng |
| **CHỈ khi SaaS đa khách** | Collection/namespace VẬT LÝ mỗi khách (cô lập cứng) | Khi bán multi-tenant nhiều pháp nhân |

**Không làm sớm (chống over-engineering):** tách collection vật lý per-user, chuyển sang Qdrant, hay
folder-per-workspace kiểu agent-ai — đều là giải sai bài toán cho on-prem một tổ chức.

---

## 8. Một dòng chốt

bravo **không nên** bắt chước "workspace thư mục" của agent-ai (đó là điểm yếu bị chính họ gắn cờ
rủi ro). Giữ **1 index + RLS-in-SQL** (thế mạnh sẵn có, đúng chuẩn enterprise), thêm **chiều
`collection`** để nhóm mềm, và đổ công vào **object storage + ingest queue + dedup/versioning +
quota** — đó mới là chỗ "nhiều tài liệu, nhiều end-user" thực sự cần.
