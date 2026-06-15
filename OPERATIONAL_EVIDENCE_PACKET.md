# OPERATIONAL EVIDENCE PACKET

This packet provides verifiable, reproducible performance evidence for the Parikshak evaluation engine. All measurements are derived from live executions of our benchmark suites under localized workloads.

---

## 1. Hardware & Software Context

- **Host Operating System**: Windows 11 Enterprise (AMD64 build 26200)
- **Python Runtime**: Python 3.11.9 (64-bit)
- **Database Engine**: SQLite 3.x with WAL (Write-Ahead Logging) enabled
- **Processor**: AMD64 Core CPU base
- **Physical Memory**: 32 GB RAM

---

## 2. Methodology

The benchmarks are executed via [tests/runtime_benchmarks.py](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/tests/runtime_benchmarks.py) and [scripts/generate_validation_packet.py](file:///d:/ISHAN/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/scripts/generate_validation_packet.py).
1. **Rule Engine Throughput**: 2,000 continuous evaluations of a standard engineering task signals payload.
2. **Concurrency Scaling**: Spawning parallel worker threads (1, 10, 50, 100 concurrent requests) hitting the rule evaluation loop.
3. **Startup Overhead**: Tracking connection time for SQLite (cold start vs. warm start) and running cryptographic event journal scans.
4. **Lock Contention**: Spawning 50 concurrent threads attempting database mutations to evaluate the throughput and delay of the single-writer queue.
5. **Storage & Memory Growth**: Tracking memory footprint changes (RSS) over 100 reviews and analyzing SQLite file sizes on disk.

---

## 3. Raw Benchmark Results

### 3.1 Throughput & Latency

- **Deterministic Evaluation Throughput**: `161,566.55 reviews/second` (`9,693,992.96 reviews/minute`)
- **Single Review Latency**: `0.006 ms`
- **Cold Start DB Init Time**: `46.12 ms`
- **Warm Start DB Init Time**: `0.98 ms`

### 3.2 Latency by Concurrency Band

| Concurrent Users | Total Duration (ms) | Avg Latency / Request (ms) | Max Latency (ms) | Throughput (req/sec) |
| :--- | :--- | :--- | :--- | :--- |
| **1 User** | 0.73 | 0.02 | 0.02 | 1,362.21 |
| **10 Users** | 1.42 | 0.02 | 0.02 | 7,059.16 |
| **50 Users** | 5.83 | 0.02 | 0.02 | 8,570.89 |
| **100 Users** | 11.23 | 0.01 | 0.02 | 8,906.46 |

### 3.3 SQLite Lock Contention Analysis

Using 50 concurrent worker threads submitting mutations to the event journal:
- **Write Throughput**: `3,732.96 writes/second`
- **Average Write Delay**: `3.84 ms`
- **Timeout or Locking Errors**: `0 errors`
- **Lock Contention Status**: **PASSED**. Single-writer mutex serialization successfully avoids database locks (`SQLITE_BUSY`).

### 3.4 Storage & Memory Growth

- **Memory Growth (100 Reviews)**: `0.0000 MB` (RSS remains constant)
- **Average JSON Event Size**: `673 bytes`
- **Database Disk Size (50 events)**: `40.0 KB` (40,960 bytes)
- **Estimated Growth per 1,000 reviews**: `0.6418 MB`

---

## 4. Conclusions

1. **Inline API Feasibility**: With a single-review latency of under `0.01 ms`, Parikshak does not add noticeable latency overhead to pipelines.
2. **Extreme Concurrency Tolerance**: Scaling up to 100 users increases evaluation throughput without increasing individual latency.
3. **Write Path Bottlenecks**: While the rule engine easily supports high concurrency, SQLite write actions are constrained to sequential execution due to the `SingleWriterQueue` locks. This limits transactional database writes to approximately `3,700 writes/sec`.
4. **Lightweight Profile**: Storage requirements are negligible, meaning the system can easily sustain millions of historical reviews on standard local SSD storage.
