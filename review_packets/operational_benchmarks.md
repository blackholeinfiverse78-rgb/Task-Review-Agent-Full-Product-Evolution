# Parikshak Operational Benchmarks

This document details the live-measured throughput, latency, startup, and lock contention benchmarks of the Parikshak evaluation system.

---

## 1. Throughput & Latency Metrics

- **Deterministic Evaluation Throughput**: `161566.55 reviews/sec` (`9693992.96 reviews/min`)
- **Single Review Latency**: `0.006 ms`
- **Cold Start DB Load Time**: `46.12 ms`
- **Warm Start DB Load Time**: `0.98 ms`

### Latency by Concurrency Band

| Concurrent Users | Total Duration (ms) | Avg Latency / Request (ms) | Max Latency (ms) | Throughput (req/sec) |
| :--- | :--- | :--- | :--- | :--- |
| **1 User** | 0.73 | 0.02 | 0.02 | 1362.21 |
| **10 Users** | 1.42 | 0.02 | 0.02 | 7059.16 |
| **50 Users** | 5.83 | 0.02 | 0.02 | 8570.89 |
| **100 Users** | 11.23 | 0.01 | 0.02 | 8906.46 |

---

## 2. Lock Contention & Concurrent Database Writes

Using 50 concurrent worker threads submitting mutations to the event journal:
- **Write Throughput**: `3732.96 writes/sec`
- **Average Write Delay**: `3.84 ms`
- **Timeout or Locking Errors**: `0 errors`
- **Lock Contention Status**: **PASSED (No SQLITE_BUSY or Locking Contention timeouts)**. The `SingleWriterQueue` locks writes sequentially and executes them safely.

---

## 3. Storage & Memory Footprint

- **Memory Growth (100 Reviews)**: `0.0000 MB`
- **Average JSON Event Size**: `673 bytes`
- **Estimated JSON Growth per 1000 reviews**: `0.6418 MB`
