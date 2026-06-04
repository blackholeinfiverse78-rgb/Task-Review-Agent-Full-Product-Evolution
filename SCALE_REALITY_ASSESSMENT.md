# Parikshak Scale Reality Assessment

This document assesses the scalability limits of Parikshak v6.0.0, classifying proven capabilities and identifying technical bottlenecks with source code evidence.

---

## 1. Scale Classification Table

| Target Reviews | Classification | Primary Evidence & Constraints |
|---|---|---|
| **100 reviews** | **PROVEN** | Handled in-memory; SQLite WAL concurrency and file lock latency are negligible. Concurrency tests run successfully. |
| **1,000 reviews** | **LIKELY** | Storage handles up to 1,000 active submissions and reviews concurrently. Writes require serializing the entire JSON state. |
| **5,000 reviews** | **NOT SUPPORTED** | Storage layer automatically evicts submissions above the 1,000 limit. The JSON serialization logic causes I/O bottlenecks. |
| **10,000 reviews** | **NOT SUPPORTED** | Same storage limits. Full database scans on boot gate check cause slow start times. |

---

## 2. Technical Evidence & Bottleneck Analysis

### 2.1 Storage Eviction Limit (1,000 Cap)
The primary constraint is in [db/persistent_storage.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/db/persistent_storage.py#L271-L293). When storing a submission, the system actively purges records if the total submissions count exceeds 1,000:
```python
def store_submission(self, submission: TaskSubmission) -> None:
    with self._file_lock:
        self._load_nolock()
        self.submissions[submission.submission_id] = submission
        
        # Enforce 1000 submissions limit
        if len(self.submissions) > 1000:
            keys = sorted(self.submissions.keys(), key=lambda k: self.submissions[k].submitted_at)
            to_evict = keys[:len(self.submissions) - 1000]
            for k in to_evict:
                self.submissions.pop(k, None)
                # Also evict corresponding reviews and next tasks
                ...
```
This hard limit means that keeping 5,000 or 10,000 reviews in active operational storage is **impossible** under the current codebase without losing data.

### 2.2 Serialized File I/O Overhead
Every database write (for submissions, reviews, or next task assignments) calls `_save_nolock()`, which dump-serializes the *entire* collection of submissions, reviews, and next tasks into a single string, writes to a `.tmp` file, calls `os.fsync()`, and replaces the file on disk:
```python
def _save_nolock(self) -> None:
    data = {
        "submissions": {k: v.model_dump(mode='json') for k, v in self.submissions.items()},
        "reviews": {k: v.model_dump(mode='json') for k, v in self.reviews.items()},
        "next_tasks": {k: v.model_dump(mode='json') for k, v in self.next_tasks.items()}
    }
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_file, self.persistence_file)
```
Writing a large JSON file on every request will cause disk write contention, slowing down evaluations.

### 2.3 Cross-Process File Lock Contention
Concurrency is managed using [db/persistent_storage.py:FileLock](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/db/persistent_storage.py#L19-L112). This class retries file creations every `0.02` seconds for up to `15.0` seconds. Under 5,000 or 10,000 reviews running concurrently, multiple worker threads will block on this lock, resulting in `TimeoutError` exceptions.

### 2.4 Boot Gate Verification Time
On every database startup, the SQLite event validator performs a full scan in [canonical_db/integrity.py:run_full_scan](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/integrity.py#L13-L144), reading every single row to verify hashes. Additionally, it scans the file backups directory for snapshot JSON files:
```python
if os.path.exists(self.backup_dir):
    for file in os.listdir(self.backup_dir):
        if file.endswith(".json") and file.startswith("snapshot_seq_"):
            ...
```
For 10,000 events, this full scan and backup traversal during startup will block API responses.
