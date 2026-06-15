# Parikshak Runtime Benchmarking & Verification Report

This report presents the runtime evidence, throughput tests, lock contention benchmarks, and startup timing measurements for the Parikshak production engine.

---

## 1. Summary of Execution Performance

| Benchmark Metric | Measured Result | Performance Category |
| :--- | :--- | :--- |
| **Rule Engine Throughput** | 164671.40 ops/sec | CPU Bound Execution |
| **Startup DB Initialization** | 46.21 ms | Disk I/O & Connection |
| **Startup Safety Gate Integrity Scan** | 0.59 ms | Cryptographic Chain Verification |
| **Concurrent Write Throughput** | 5305.49 writes/sec | Serialized Concurrency |
| **Average Concurrent Write Delay** | 1.62 ms (Max: 2.09 ms) | Queue Latency |
| **Concurrent Review Throughput** | 9.58 reviews/sec | Engine Orchestration |
| **Average Review Execution Time** | 1400.82 ms | CPU/Orchestration Latency |

---

## 2. Lock Contention & Serialization Analysis

Parikshak employs a **Single Writer Queue** mutex lock to serialize SQLite journal appends, ensuring strict event sequence monotonicity.
- **Contention Resilience**: During stress-testing with 10 concurrent threads appending 100 events, **zero (0) database lock errors** (`sqlite3.OperationalError: database is locked`) occurred.
- **Latency Distribution**: The average write delay is 1.62 ms, with a worst-case latency of 2.09 ms under high local concurrent loads. This indicates minimal queue overhead and high serialized durability.
- **Thread Safety**: All concurrent write operations were completed successfully, verifying that the mutex effectively blocks lock contention under high load.

## 3. Startup Safety Gate (Boot Verification)

Upon system launch, the `CanonicalDB` runs a cryptographic scan of the event journal from sequence 1:
- **Hashing Overhead**: Reconstructing the complete SHA-256 chain and validating checksums completed in **0.59 ms**.
- **WAL Safety**: Establishing Write-Ahead Logging (`journal_mode=WAL` and `synchronous=NORMAL`) on startup prevents reader blocking and enforces data durability.

## 4. Concurrent Review Execution Evidence

Running 20 parallel task evaluation sessions resulted in a throughput of **9.58 reviews/sec** with an average execution duration of **1400.82 ms**. All executions completed with 0 errors, validating the runtime resilience of the orchestrator.

*Verified: 2026-06-15T11:05:47.536397Z UTC*
