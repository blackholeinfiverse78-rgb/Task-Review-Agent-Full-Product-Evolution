# Governance Contract (Gov-OS Contract)

- **Version**: 1.0.0
- **Status**: FROZEN / CORE-LOCKED
- **Ownership Boundary**: Owned by `canonical_db/pipeline.py` and `canonical_db/db.py`.

---

## 1. Purpose
Governs all mutations made to the persistent system journal (Gov-OS ledger). It enforces that no mutation can be committed without a cryptographic envelope signed by an authorized human governor. The storage engine enforces append-only monotonicity via database triggers, blocking updates and deletes.

---

## 2. Authorized Governor Directory
Only the following hard-coded actors are permitted to sign and authorize governance mutations:

- `"Akash"`
- `"Sri Satya"`
- `"Nupur"`
- `"Senior Operator"`
- `"Reviewer-1"`
- `"Reviewer-2"`
- `"operator-1"`
- `"Vinayak"` (added via ecosystem mapping compatibility)

*Note: Autonomous systems (e.g. `"AI_Orchestrator_Agent"`) are explicitly blocked from signing release transactions.*

---

## 3. Ingestion Envelope Schema
Mutations must be wrapped in a `GovernanceEnvelope` structured payload:

| Field | Type | Range / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `trace_id` | String | Min 8 chars | Inherited from Niyantran upstream |
| `schema_version` | String | Default: `"v1.0"` | Schema compatibility version |
| `actor` | String | Non-empty | Operator executing the transaction |
| `actor_role` | String | Non-empty | Role classification |
| `timestamp` | String | ISO-8601 UTC format | Timing audit mark |
| `lineage_reference`| String | Non-empty | Back-reference to source documentation |
| `authorized_by` | String | Must be in Governor Directory | Governor signature |
| `event_type` | String | e.g. `"review_history"` \| `"assignment_history"` | Transaction event type |
| `payload` | Dict | Valid JSON structure | The payload details to commit |
| `parent_event_hash`| String | 64-character hex string | The SHA-256 hash of the previous head event |

---

## 4. Ingest & Mutation Outputs
Upon committing the mutation, the pipeline returns a synchronized receipt:

```json
{
  "status": "SUCCESS",
  "sequence": 4,
  "event_id": "evt-f87c12b9a7c3",
  "event_hash": "8d4eeea32de1ed3e12d0364a3935456349f5746424d205977ba06b7968adf68e",
  "snapshot": "snapshot_seq_4_hash_8d4eeea3.sqlite"
}
```

---

## 5. Security & SQLite Trigger Constraints
The SQLite engine is compiled with strict data triggers preventing tampering:

```sql
CREATE TRIGGER prevent_update_events
BEFORE UPDATE ON events
BEGIN
  SELECT RAISE(FAIL, 'MUTATION_BLOCKED: UPDATE operations are forbidden on the immutable event ledger.');
END;

CREATE TRIGGER prevent_delete_events
BEFORE DELETE ON events
BEGIN
  SELECT RAISE(FAIL, 'MUTATION_BLOCKED: DELETE operations are forbidden on the immutable event ledger.');
END;
```

---

## 6. Failure States
All contract violations trigger immediate transaction rollbacks.

### 6.1 Unauthorized Governor (HTTP 403 Forbidden)
- **Trigger**: `authorized_by` not in authorized directory, or empty.
- **Payload**:
  ```json
  {
    "detail": "GOVERNANCE_REJECT: Actor 'External_Product' is not authorized to sign-off on governance events."
  }
  ```

### 6.2 Concurrent Update Collision / Out of Order Sequence (HTTP 409 Conflict)
- **Trigger**: `parent_event_hash` does not match the hash of the current database head event (OCC lock collision).
- **Payload**:
  ```json
  {
    "detail": "GOVERNANCE_LOCK_REJECT: Concurrent modification detected. Expected head hash '8d4eee...', got '2c5aaa...'"
  }
  ```

---

## 7. Versioning Rules
- **Governance Envelope Schema Key**: Governed by the `schema_version` inside the governance envelope.
- **Increment Policy**: Bumping schema structure or changing allowed events requires a major schema version bump. Adding optional payload fields requires a minor version bump.

---

## 8. Compatibility Rules
- **Backward Compatibility**: The mutation engine must support older valid event schema versions.
- **Validation Constraints**: Any new governors added to the allowlist are forward-compatible. System updates must not break historical sequence validation.

---

## 9. Ownership Boundary
- **Parikshak Boundary**: Verifies signatures, computes SHA-256 hashes, maintains trigger constraints, creates snapshots.
- **Consumer Boundary**: Consumers cannot call the mutate endpoint directly without generating a correct envelope signed by an authorized governor.
