# DEMO18-02 live Knowledge Chat SSE evidence

Status: `RUNTIME PASS — local SSE and browser lifecycle verified; broader hardening/rehearsal remain open`

Date: 2026-08-03

## Runtime

- Containerized API completed startup and served the synthetic local runtime.
- The authenticated probe uses a freshly generated conversation ID and the supported password-login
  path. It does not print the token, credential value, prompt or answer content.
- Applied database revision remains `0020_case_v2_audit (head)`.

## SSE result

`PYTHONPATH=. python scripts/demo18_chat_probe.py` inside `bravo-v2-api-1` produced:

```json
{"terminal_done": true, "error_events": 0, "source_events": 1, "answer_events": 5}
```

This proves one actual authenticated POST-SSE turn reaches a terminal `done` event and emits source
and answer events without a fixture provider. The independent browser proof now covers durable
reload, synthetic attachment readiness, citation selection, feedback and read-only share; see
[DEMO18-08-LIVE-BROWSER-2026-08-03.md](DEMO18-08-LIVE-BROWSER-2026-08-03.md). It does not establish
model-quality, SME, pilot or production gates.

## Probe controls

- The probe is [demo18_chat_probe.py](../../scripts/demo18_chat_probe.py).
- It emits aggregate event metadata only; no token, password, source text or generated answer is
  written to evidence/log output.
