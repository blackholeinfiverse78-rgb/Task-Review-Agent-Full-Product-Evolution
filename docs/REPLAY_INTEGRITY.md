# REPLAY INTEGRITY MODEL

## 1. INTEGRITY MODEL
Replay engine acts as the operational truth reconstructor.
- It parses append-only `storage/audit_logs/`.
- Every transition event requires an explicit `trace_id`.
- Every payload requires an integrated JSON-deterministic SHA-256 `_checksum`.

## 2. FORENSIC VALIDATION
- `verify_audit_log`: Reads the file, parses JSON, and re-computes `_checksum`. Reports corrupt line numbers explicitly without failing the entire valid log segment.
- `verify_checkpoint_chain`: Reads deterministic checkpoints from `storage/checkpoints/` and validates timestamp continuity and structural integrity.

## 3. DIVERGENCE HANDLING
- Compares original evaluated output against replayed output.
- Target fields: `evaluation_result`, `failure_type`, `selected_task_id`, `source`.
- Raises `REPLAY_DIVERGENCE` loudly if drift occurs, refusing to allow mutated execution.

## 4. CORRUPTION RECOVERY
- Interrupted writes resulting in truncated JSON (`JSONDecodeError`) are isolated.
- The `partial_recovery` mechanism skips invalid lines and preserves the remaining valid lineage, allowing the system to continue parsing uncorrupted operational history.
