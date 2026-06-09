# Parikshak Operational Benchmarks

This document details the live-measured throughput, latency, startup, and lock contention benchmarks of the Parikshak evaluation system.

---

## 1. Throughput & Latency Metrics

- **Deterministic Evaluation Throughput**: `140386.34 reviews/sec` (`8423180.60 reviews/min`)
- **Single Review Latency**: `0.007 ms`
- **Cold Start DB Load Time**: `6.02 ms`
- **Warm Start DB Load Time**: `1.94 ms`

### Latency by Concurrency Band

| Concurrent Users | Total Duration (ms) | Avg Latency / Request (ms) | Max Latency (ms) | Throughput (req/sec) |
| :--- | :--- | :--- | :--- | :--- |
| **1 User** | 0.77 | 0.02 | 0.02 | 1294.50 |
| **10 Users** | 1.47 | 0.02 | 0.03 | 6810.13 |
| **50 Users** | 6.97 | 0.02 | 0.02 | 7169.69 |
| **100 Users** | 13.71 | 0.02 | 0.03 | 7294.42 |

---

## 2. Lock Contention & Concurrent Database Writes

Using 50 concurrent worker threads submitting mutations to the event journal:
- **Write Throughput**: `2747.83 writes/sec`
- **Average Write Delay**: `5.98 ms`
- **Timeout or Locking Errors**: `0 errors`
- **Lock Contention Status**: **PASSED (No SQLITE_BUSY or Locking Contention timeouts)**. The `SingleWriterQueue` locks writes sequentially and executes them safely.

---

## 3. Storage & Memory Footprint

- **Memory Growth (100 Reviews)**: `0.0039 MB`
- **Average JSON Event Size**: `673 bytes`
- **Estimated JSON Growth per 1000 reviews**: `0.6418 MB`
