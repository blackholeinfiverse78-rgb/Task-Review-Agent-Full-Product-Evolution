# Constitutional Governance Boundary Document — Parikshak v6.0.0

## Core Boundary Rules

1. **Parikshak Cannot Approve** — Zero approval authority. All state mutations require explicit human sign-off from an authorized governor in `AUTHORIZED_GOVERNORS`.
2. **Parikshak Cannot Assign Autonomously** — Task assignment releases are blocked. `AutonomousReleaseBlocked` raised on any non-human actor attempting `assignment_history` commits.
3. **Parikshak Cannot Self-Govern** — Cannot mutate its own rules, schema definitions, `AUTHORIZED_GOVERNORS`, or verification logic at runtime. `FrozenRegistry` enforces this at the schema layer.
4. **Parikshak Cannot Become Source of Truth** — All state is derived from the append-only event journal via deterministic replay. No hidden caches, no authority flags outside the journal.
5. **Parikshak Cannot Execute Hidden Prioritization** — All evaluation is deterministic rule-based. `StrategicApprovalEngine` produces advisory recommendations only. `execution_blocked=True` on every recommendation.
6. **Parikshak Cannot Self-Modify Contracts** — No API endpoint modifies `AUTHORIZED_GOVERNORS`, `ROLE_PERMISSIONS`, `ENTITY_SCHEMAS`, or `IRREVERSIBLE_STATES`.

---

## GPT Bridge Boundary

**Allowed operations:**
- `export_state_for_gpt()` — read-only signed state export, no DB write
- `prepare_import_envelope()` — schema validation + envelope wrapping, returns `AWAITING_HUMAN_APPROVAL`, no DB write

**Blocked operations (raises immediately):**
- Any direct `CanonicalDB.append_event()` call
- Any approval or assignment authority
- Any mutation of `AUTHORIZED_GOVERNORS`
- Any replay, rollback, or snapshot execution
- Any snapshot creation or restore

**Synchronization ownership:**
- GPT receives a signed read-only snapshot of current state
- GPT may propose scaffolds via `prepare_import_envelope()`
- All proposed scaffolds return `status=AWAITING_HUMAN_APPROVAL`
- Human operator is the sole authority to submit the envelope to `GovernedPipeline`

**Replay implications:**
- GPT exports do NOT create journal events
- GPT scaffolds do NOT create journal events
- Only human-approved `GovernedPipeline.submit_mutation()` creates journal events

**Backup interaction:**
- GPT bridge has no access to `BackupManager`
- GPT bridge cannot trigger snapshots or restores

---

## Gov-OS Scope Restraint

Gov-OS is infrastructure, not authority. The following restraints are mandatory:

**Permitted:**
- Append-only event journal writes (human-approved only)
- Integrity scanning at boot and before writes
- Snapshot creation after each governed mutation
- Snapshot restore with parity verification
- Read-only state export
- Observability logging (non-blocking)

**Prohibited:**
- Autonomous assignment or approval
- Silent authority expansion via convenience mutations
- Operational legitimacy assumptions (Gov-OS presence ≠ Gov-OS authority)
- Hidden prioritization via journal ordering manipulation
- Self-modification of governance constants

**Scope creep warning signals:**
- Any new API endpoint that writes to the journal without `authorized_by` in `AUTHORIZED_GOVERNORS`
- Any new field added to `AUTHORIZED_GOVERNORS` without explicit human decision
- Any new `event_type` added to `ENTITY_SCHEMAS` without schema manifest registration
- Any mutation path that bypasses `GovernedPipeline.submit_mutation()`

---

## System Enforcement Checks

| Enforcement | Location | Mechanism |
|---|---|---|
| Autonomous release blocked | `canonical_db/pipeline.py` + `canonical_db/db.py` | `AutonomousReleaseBlocked` raised |
| Missing authorization rejected | `canonical_db/pipeline.py` | `PermissionError` raised |
| Schema mutation blocked | `canonical_db/contracts.py` | `FrozenRegistry` raises `TypeError` |
| Runtime schema drift rejected | `canonical_db/integrity.py` | Pydantic validation on every scan |
| Boot corruption blocked | `canonical_db/db.py` | `STARTUP_SAFETY_GATE_BLOCKED` raised |
| Concurrent write serialized | `canonical_db/db.py` | `SingleWriterQueue` threading.Lock |
| Snapshot parity verified | `canonical_db/backup.py` | `RESTORE_PARITY_MISMATCH` raised |
| GPT write authority | `canonical_db/gpt_bridge.py` | No `append_event()` call path exists |
| Constitutional validation | `governance_layer/governance.py` | `ConstitutionalValidator.validate()` |
