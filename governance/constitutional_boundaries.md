# Constitutional Governance Boundary Document

## Boundary Rules and Enforcement

Parikshak is a governed engineering analysis system designed to operate with strict local-first, append-only event sourcing and human-in-the-loop validation constraints. The system operates under the following non-negotiable boundaries:

1. **Parikshak Cannot Approve**: Parikshak has zero approval authority. All state mutations and reviews require explicit human approval and verification from an authorized governor.
2. **Parikshak Cannot Assign**: Autonomous release or assignment of tasks is strictly blocked. Task assignments must be explicitly initiated by human action and confirmed via human-signed governance envelopes.
3. **Parikshak Cannot Self-Govern**: The system cannot mutate its own rules, boundaries, schema definitions, or verification logic at runtime.
4. **Parikshak Cannot Become the Source of Truth**: The database and event logs are derived from human-validated actions. Parikshak does not store hidden cache states, authority flags, or unverified logs that bypass the human governance gate.

## System Enforcement Checks

- **Autonomous Release Rejection**: Any attempt to perform a task release or commit an `assignment_history` event without human sign-off triggers an `AutonomousReleaseBlocked` exception.
- **Single-Writer Mutex Queue**: Serializes all database mutation operations, ensuring deterministic write-ordering and preventing concurrent race conditions from modifying the log.
- **Immutable Triggers**: Triggers prevent `UPDATE` and `DELETE` queries on the events journal, protecting history from modification.
- **Integrity Safety Gate**: Verifies SHA-256 chain integrity, parent-child event links, schema drift, snapshot divergence, and checkpoint alignment at every boot, halting initialization on failure.
