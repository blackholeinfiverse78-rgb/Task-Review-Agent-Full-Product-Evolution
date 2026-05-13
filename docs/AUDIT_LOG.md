# Audit Log Documentation

---

## Location

```
storage/audit_logs/audit_YYYY-MM-DD.jsonl
```

One file per day. New file created automatically at midnight.

---

## Schema (6 Fields — Exact)

```json
{
  "trace_id":      "string — upstream trace_id from submission",
  "submission_id": "string — submission identifier",
  "system_task":   "string — task selected by deterministic engine",
  "final_task":    "string — task actually assigned (or NONE)",
  "action":        "string — approve | reject | modify",
  "timestamp":     "string — ISO datetime of action"
}
```

---

## Field Semantics

| Field | approve | reject | modify |
|---|---|---|---|
| `system_task` | deterministic recommendation | deterministic recommendation | deterministic recommendation |
| `final_task` | same as system_task | `"NONE"` | override_task_id |
| `action` | `"approve"` | `"reject"` | `"modify"` |

`system_task` is always the original deterministic recommendation, regardless of action. This allows auditing of how often human decisions diverge from the system.

---

## Implementation

**File:** `api/review_routes.py`

```python
def log_audit(entry: AuditLogEntry):
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(AUDIT_LOG_DIR, f"audit_{date_str}.jsonl")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry.model_dump(), default=str) + "\n")
```

- Mode `"a"` — append only, never overwrites
- One JSON object per line (JSONL format)
- `default=str` handles datetime serialization

---

## Real Entries (from `storage/audit_logs/audit_2026-05-07.jsonl`)

```jsonl
{"trace_id": "test-trace-001", "submission_id": "sub-aeb3f363fdf5-race-001", "system_task": "T-GOV-F01", "final_task": "T-GOV-F01", "action": "approve", "timestamp": "2026-05-07 17:00:08.227760"}
{"trace_id": "test-trace-002", "submission_id": "sub-aeb3f363fdf5-race-002", "system_task": "T-GOV-F01", "final_task": "T-GOV-OVERRIDE", "action": "modify", "timestamp": "2026-05-07 17:00:08.247637"}
```

---

## Guarantees

- Every approve, reject, and modify action writes exactly one entry
- No action is silent — missing audit entry = bug
- Entries are never deleted or modified after writing
- `system_task` is captured before any mutation, so it always reflects the original recommendation
- For modify: `system_task != final_task` — this is the divergence record

---

## Reading the Log

```bash
# Windows — today's log
type storage\audit_logs\audit_2026-05-07.jsonl

# Unix — today's log
cat storage/audit_logs/audit_$(date +%Y-%m-%d).jsonl

# Pretty print with jq (Unix)
cat storage/audit_logs/audit_$(date +%Y-%m-%d).jsonl | jq .

# Count entries
cat storage/audit_logs/audit_$(date +%Y-%m-%d).jsonl | wc -l
```

---

## AuditLogEntry Model

**File:** `models/review_models.py`

```python
class AuditLogEntry(BaseModel):
    trace_id:      str
    submission_id: str
    system_task:   str
    final_task:    str
    action:        str
    timestamp:     datetime = Field(default_factory=datetime.now)
```
