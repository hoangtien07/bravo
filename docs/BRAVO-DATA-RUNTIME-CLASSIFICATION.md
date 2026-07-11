# BRAVO Data Runtime Classification

Tai lieu nay la chuan phan loai data cho BRAVO AI agent runtime. Muc tieu la giu
RAG corpus gon, co metadata, co citation, va khong nap nham du lieu rieng vao scope
GLOBAL.

Policy chay that nam tai:

```text
file_system/bravo_data_runtime_policy.yaml
```

Code audit/readiness doc file policy nay, vi vay thay doi class/path phai sua YAML truoc,
khong hard-code trong docs. Policy la ban do va guardrail; no khong tu mount file tren VM.
Docker compose, systemd, hoac bien moi truong deploy moi la noi tao/mount duong dan runtime.

## Runtime Path Resolution

Policy dung bien moi truong de chay duoc tren local, Docker, VM:

| Bien | Mac dinh khi khong set | Docker compose |
|---|---|---|
| `APP_ROOT` | current working directory | `/app` |
| `DATA_ROOT` | `${APP_ROOT}/data` | `/app/data` |
| `CORPUS_ROOT` | `${APP_ROOT}/file_system` | `/app/file_system` |
| `UPLOAD_ROOT` | `${DATA_ROOT}/uploads` | `/app/data/uploads` |
| `PRIVATE_DATA_ROOT` | `${DATA_ROOT}/private` | `/app/data/private` |
| `DATA_RUNTIME_POLICY` | `${APP_ROOT}/file_system/bravo_data_runtime_policy.yaml` | `/app/file_system/bravo_data_runtime_policy.yaml` |

Startup boot guard se:

- doc va validate `DATA_RUNTIME_POLICY`;
- fail neu required path thieu, manifest thieu file, active corpus bi duplicate;
- tu tao path co `ensure_exists: true`, hien tai la upload/private runtime dirs;
- khong tao shared corpus hay rule path, vi cac path do phai di theo repo/image/mount.

## Nguyen Tac

- `file_system/` la active shared knowledge corpus. Chi file co trong
  `file_system/bravo_corpus_manifest.yaml` moi duoc ingest mac dinh.
- File nam ngoai manifest khong bi xoa tu dong, nhung bi bo qua trong manifest-only
  ingest va duoc readiness audit canh bao.
- Data van hanh, demo, local, customer-specific khong duoc nap GLOBAL vao vector DB.
- Derived summaries chi duoc giu khi co loi ich ro trong eval; citation nen uu tien
  tai lieu goc.

## Cac Lop Data

| Class | Vi tri | Owner | Duoc version | Duoc ingest shared RAG |
|---|---|---|---|---|
| `shared_knowledge` | `file_system/` + manifest | BRAVO domain/product | Co | Co, neu nam trong manifest |
| `domain_rules` | `app/accounting/data/` | Accounting/compliance | Co | Khong, dung boi engine/rule loader |
| `eval_fixtures` | `tests/fixtures/` | Engineering/QA | Co | Khong, chi dung test/eval |
| `private_operational_data` | `data/private/...` hoac local ignored samples | Customer/site/local owner | Khong mac dinh | Khong mac dinh; phai co scope/RLS rieng |
| `runtime_uploads` | `data/uploads/...` | End user/runtime | Khong | Khong vao GLOBAL; xu ly theo user/session/RLS |
| `derived_summary` | Mindmap/summary co kiem soat | Domain team | Co neu can | Chi khi manifest khai bao va eval chung minh huu ich |

## Cau Hinh Policy

`file_system/bravo_data_runtime_policy.yaml` gom 4 phan:

- `classes`: dinh nghia 6 lop runtime bat buoc.
- `path_rules`: gan path vao class va quy tac ingest/duplicate.
- `source_type_classes`: map `source_type` trong manifest sang data class.
- `required_classes`: guard de readiness fail neu thieu lop chuan.

Path rules dang ap dung:

| Path | Class | Chinh sach |
|---|---|---|
| Path policy | Class | Chinh sach |
|---|---|---|
| `${CORPUS_ROOT}` | `shared_knowledge` | manifest-only, active duplicate la loi |
| `${CORPUS_ROOT}/Data` | `private_operational_data` | giu local/demo data, canh bao neu ingestible |
| `${APP_ROOT}/app/accounting/data` | `domain_rules` | versioned rule artifacts, khong ingest RAG |
| `${APP_ROOT}/tests/fixtures` | `eval_fixtures` | chi dung test/eval, optional trong production |
| `${PRIVATE_DATA_ROOT}` | `private_operational_data` | ignored location cho data rieng, auto-create |
| `${UPLOAD_ROOT}` | `runtime_uploads` | runtime uploads theo user/session/RLS, auto-create |

## Chinh Sach Ingest

- Lenh mac dinh:

```powershell
python -m scripts.ingest_userguide file_system
```

  chi nap file co trong manifest.

- `--allow-unmanifested` chi dung cho import co scope ro, vi du phong ban hoac bo du
  lieu tam thoi da duoc chap thuan:

```powershell
python -m scripts.ingest_userguide path\to\scoped_docs --department "Support" --allow-unmanifested
```

- `file_system/Data/*.md` la private/demo/operational sample, khong nam trong manifest
  va khong duoc nap vao shared RAG.

## Audit

Chay readiness truoc demo/ingest:

```powershell
python -X utf8 -m app.eval.bravo_readiness
```

Chay audit rieng khi don data:

```powershell
python -X utf8 -m app.eval.bravo_data_audit
```

Audit bao:

- file trong `file_system` nhung khong nam trong manifest;
- file manifest tro toi nhung thieu tren dia;
- so file theo tung runtime data class (`files_by_class`);
- duplicate SHA-256 trong toan bo corpus;
- duplicate SHA-256 trong active manifest corpus, day la loi can sua;
- summary/derived source co nguy co thay the citation goc.
