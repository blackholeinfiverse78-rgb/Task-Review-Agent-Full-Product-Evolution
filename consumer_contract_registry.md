# Consumer Contract Registry

- **Registry Version**: 1.0.0
- **Status**: FROZEN / REGISTRY-LOCKED
- **Registry Date**: 2026-06-12

---

## 1. Unified Contract Directory
This registry records the specifications and repository paths of the five frozen operational contracts governing consumer interactions with Parikshak.

| Contract Name | Path | Target Interfaces | Key Operations |
| :--- | :--- | :--- | :--- |
| **Review Contract** | [review_contract.md](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/contracts/review_contract.md) | Niyantran Ingestion Queue | `POST /niyantran/submit` |
| **Assignment Contract** | [assignment_contract.md](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/contracts/assignment_contract.md) | Task Graph Traversal | `select_next_task()` |
| **Escalation Contract** | [escalation_contract.md](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/contracts/escalation_contract.md) | Confidence Calculation | `calculate_confidence()` |
| **Governance Contract** | [governance_contract.md](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/contracts/governance_contract.md) | Gov-OS Immutable Mutate | `POST /gov-os/mutate` |
| **Export Contract** | [export_contract.md](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/contracts/export_contract.md) | Downstream Ledgers | `propagate_governed_approval()` |

---

## 2. Ingestion Request Schema (Review Contract)
```json
{
  "task_id": "string",
  "task_title": "string",
  "task_description": "string",
  "submitted_by": "string",
  "repository_url": "string (optional)",
  "trace_id": "string (min 8 chars, mandatory)"
}
```

## 3. Ingestion Receipt Schema (Review/Assignment Outcome)
```json
{
  "trace_id": "string",
  "submission_id": "string",
  "evaluation_result": "PASS | FAIL",
  "failure_type": "string | null",
  "selected_task_id": "string",
  "selection_reason": "string",
  "source": "task_graph"
}
```

## 4. Governance Envelope Ingestion Schema (Gov-OS)
```json
{
  "trace_id": "string",
  "schema_version": "string",
  "actor": "string",
  "actor_role": "string",
  "timestamp": "string",
  "lineage_reference": "string",
  "authorized_by": "string (must match AUTHORIZED_GOVERNORS)",
  "event_type": "string",
  "payload": "object",
  "parent_event_hash": "string"
}
```

---

## 5. Drift & Compliance Monitoring
- **Drift Checks**: Checked automatically during system startup (`db.scan_and_verify()`). Any schema variance halts the uvicorn startup procedure.
- **Contract Enforcement**: Handled via strict Pydantic model validation at api ingress.
