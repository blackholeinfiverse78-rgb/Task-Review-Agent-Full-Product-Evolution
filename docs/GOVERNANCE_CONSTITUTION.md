# 📜 Governance Constitution (Gov-OS Boundaries)

This document declares the strict constitutional boundaries of Parikshak. Under no circumstances may these constraints be bypassed.

---

## 1. Absolute Boundary Rules

### Rule 1: Parikshak Cannot Approve
- The system has **zero approval authority**.
- All state mutations and reviews require explicit human approval (`HUMAN_APPROVED`) signed off by an authorized governor.

### Rule 2: Parikshak Cannot Assign
- Autonomous release or assignment of tasks is **strictly blocked**.
- Any attempt to release or commit a task assignment without human sign-off triggers an `AutonomousReleaseBlocked` exception.

### Rule 3: Parikshak Cannot Self-Govern
- The system **cannot mutate its own rules, boundaries, or schemas** at runtime.
- The schema registry is frozen at startup to prevent dynamic mutations.

### Rule 4: Parikshak Cannot Become the Source of Truth
- Parikshak's event database is derived from human-validated actions.
- The system does not maintain hidden state flags, unverified cache databases, or authority bypasses.

---

## 2. GPT Bridge Quarantine Boundaries

The GPT bridge is isolated under the following rules:
- **Export-Only**: The bridge is permitted to export signed state snapshots to GPT interfaces.
- **No Direct DB Mutations**: The bridge cannot mutate the SQLite database.
- **Quarantined Imports**: Any import from GPT must be converted to a draft scaffold event envelope with the status `AWAITING_HUMAN_APPROVAL`. It requires explicit manual sign-off by a human operator to be committed to the log.
- **No Governance Authority**: The GPT bridge holds no approval or assignment authority.

---

## 3. Human Approval Enforcement Lock

The system enforces assignment locks before task release:
```python
if approval_state != "HUMAN_APPROVED":
    raise AutonomousReleaseBlocked("AI release of assignments is strictly prohibited.")
```
Any transaction violating this lock is rejected and rolled back immediately.
