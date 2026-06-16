# Capability Governance Packet

- **Version**: 1.0.0
- **Status**: ACTIVE / HARDENED
- **Module Ownership**: `canonical_db/pipeline.py`

---

## 1. Governance Control Directory

### 1.1 Authorized Governors Allowlist
All persistent mutations modifying the system state must be approved by one of the following authorized human actors:

1. **Akash**
2. **Sri Satya**
3. **Nupur**
4. **Senior Operator**
5. **Reviewer-1**
6. **Reviewer-2**
7. **operator-1**
8. **Vinayak**

*AI agents are strictly blocked from signing release transactions. Direct updates without an approved governor signature will raise PermissionError at the pipeline level.*

---

## 2. SQLite Database Immutability Triggers
The SQLite storage engine enforces append-only monotonicity. The SQL schema compiles strict triggers:

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

## 3. Cryptographic Chain Checkpoint (OCC Logic)
To ensure sequence monotonicity and prevent out-of-order writes:
1. Every event envelope carries a `parent_event_hash` linking to the previous head hash of the ledger.
2. The pipeline computes the SHA-256 hash of the payload:
   $$\text{event\_hash} = \text{SHA256}(\text{canonical\_json}(\text{payload}))$$
3. If the incoming `parent_event_hash` does not match the stored head, the transaction aborts with `GOVERNANCE_LOCK_REJECT`.

---

## 4. Verification Proof Log
The readiness validation suite (`scratch/test_ecosystem_readiness.py`) runs verification tests for all triggers and ceilings.
```
--- 1. TESTING AUTHORITY CEILINGS ---
[+] SUCCESS: Unauthorised human mutation blocked as expected. 
    Error: GOVERNANCE_REJECT: Actor 'Hacker_Bob' is not authorized to sign-off on governance events.
[+] SUCCESS: Autonomous release blocked as expected. 
    Error: AutonomousReleaseBlocked: Actor 'AI_Orchestrator_Agent' is not authorized to sign-off on governance events.

--- 2. TESTING DATABASE IMMUTABILITY (TRIGGERS) ---
[+] SUCCESS: UPDATE operation blocked by trigger. Error: UPDATE operation not allowed on append-only event journal
[+] SUCCESS: DELETE operation blocked by trigger. Error: DELETE operation not allowed on append-only event journal
```
*Proof status: PASS*
