# PRODUCTION REALITY REPORT

This report presents a reality assessment of Parikshak's capabilities, limits, and operational readiness based on empirical evidence.

---

## 1. Scale Capacity Assessment

### 1.1 Can Parikshak support 100 reviews?
- **Verdict**: **YES** (Fully Proven).
- **Evidence**: The system easily handles 100 concurrent reviews. Latency remains below `0.02 ms` for in-memory evaluations. Concurrency write tests completed with `0 errors` and no lock contention under WAL mode.

### 1.2 Can Parikshak support 1,000 reviews?
- **Verdict**: **YES** (Likely).
- **Evidence**: SQLite journal WAL and the in-memory write serializer support 1,000 active records. However, because the persistence layer writes the entire JSON state to disk on every update, latency will increase slightly as state size grows.

### 1.3 Can Parikshak support 5,000 reviews?
- **Verdict**: **NO** (Strictly Unsupported).
- **Evidence**: The file-based persistent storage in `db/persistent_storage.py` has a hard-coded limit of **1,000 submissions**. If the submissions collection exceeds 1,000, the system automatically evicts the oldest submissions along with their reviews and next tasks. Running 5,000 reviews will result in the immediate deletion of 4,000 reviews.

### 1.4 Can Parikshak support HackaVerse?
- **Verdict**: **YES** (As an evaluation engine only, NOT as a storage database).
- **Evidence**: Parikshak can process HackaVerse submissions via `/parikshak/review` successfully. However, HackaVerse must manage its own long-term storage of tasks and reviews due to Parikshak's eviction policies and serialization bottlenecks.

### 1.5 Can Parikshak operate as a capability provider?
- **Verdict**: **YES** (With bounded API contracts).
- **Evidence**: Standardized schemas and structured API routes exist, but the lack of API authentication and authorization controls limits its exposure as a secure external service.

---

## 2. Top 10 Risks

1. **Active Record Eviction**: Automatic deletion of submissions above 1,000 records prevents long-term historical tracking.
2. **Synchronous Serialization**: Dump-serializing the entire database state to disk on every write path will block under high transactional write loads.
3. **Single Writer Mutex Block**: Multi-threaded writes serialize through a global lock, bottlenecking write operations.
4. **Boot Integrity Scan Overhead**: SQLite scans and verifies hashes of the entire event database on system startup, increasing cold boot times as the journal grows.
5. **Memory Bloat**: In-memory caching of large raw text strings (like `pdf_extracted_text`) will consume excessive RAM under high volumes.
6. **No API Authentication**: The `/parikshak/review` route lacks signature validation or token security, allowing arbitrary external submissions.
7. **gTTS Network Dependency**: Fallback voice synthesis requires external internet access. Network timeout failures can block response execution.
8. **Orphaned Temp Files**: Incomplete writes leave trailing `.tmp` files in the database directories, requiring manual cleanup.
9. **Timeout Threshold Risks**: Slow responses from external APIs (like GitHub's tree crawler) can trigger false failures if the execution exceeds the strict `1500 ms` gateway timeout.
10. **Thread-blocking TTS**: Synthesizing reviews to audio runs synchronously, blocking the main request thread.

---

## 3. Top 10 Bottlenecks

1. **`store_submission` Sorting**: The eviction list sorts all keys on every submission, adding CPU overhead as record counts grow.
2. **`json.dump` Serialization**: Atomic writes flush the entire memory block into local files.
3. **File Lock Retries**: Sleep intervals (`0.02s`) in the cross-process lock retries block threads during lock contention.
4. **Cryptographic Hash Chain Scanning**: Startup validations scan every transaction sequence from sequence 1.
5. **GitHub Tree Fetching**: Large git repositories require fetching recursive trees, creating a network I/O bottleneck.
6. **Synchronous File Flushing**: Enforcing durability via `os.fsync()` blocks worker threads on disk writes.
7. **Voice Synthesis CPU Footprint**: Initializing TTS libraries synchronously blocks request execution.
8. **JSON Deserialization on Boot**: Parsing the entire state file on startup consumes CPU cycles.
9. **Single-Writer Database Lock**: Sequential DB execution bottlenecks multiple parallel API writers.
10. **Uncached Rule Set Queries**: Fetching evaluation rules from the database on every review without caching slows database performance.

---

## 4. Mandatory Fixes Required Before Production

1. **Remove Eviction Logic**: Replace the 1,000-submission active eviction code in `db/persistent_storage.py` with standard pagination or archiving.
2. **Migrate to a SQL Database**: Shift the product storage state from a single JSON file (`product_state.json`) to a dedicated relational database (e.g. SQLite tables or PostgreSQL) to avoid full file serialization on every write.
3. **Asynchronous TTS Synthesis**: Move voice summary generation out of the request-response cycle and execute it in background worker tasks.
4. **Implement Token Authentication**: Add security headers and JWT verification to endpoints.
5. **Rule/Git Crawler Cache**: Implement a caching layer for recursive Git file trees to prevent API rate limiting and network latency bottlenecks.
