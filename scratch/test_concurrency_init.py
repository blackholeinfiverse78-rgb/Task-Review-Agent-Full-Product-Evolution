import sys
import os
import threading

sys.path.append(os.getcwd())

from scripts.generate_proofs import make_valid_envelope
from canonical_db.pipeline import GovernedPipeline
from canonical_db.db import CanonicalDB

concurrent_db = "storage/concurrent_test.sqlite"
if os.path.exists(concurrent_db):
    os.remove(concurrent_db)

# Pre-initialize database to create table
db = CanonicalDB(concurrent_db)
db.close()

pipeline_c = GovernedPipeline(concurrent_db)

exceptions = []
exceptions_lock = threading.Lock()

def worker(idx):
    env = make_valid_envelope()
    env.payload["candidate_id"] = f"cand-{idx}"
    env.payload_checksum = env.compute_checksum()
    env.checksum = env.payload_checksum
    try:
        pipeline_c.submit_mutation(env, "operator-1")
    except Exception as e:
        with exceptions_lock:
            exceptions.append((idx, type(e).__name__, str(e)))

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Total exceptions: {len(exceptions)}")
for idx, exc_type, exc_msg in exceptions:
    print(f"Worker {idx} raised {exc_type}: {exc_msg}")

db_check = CanonicalDB(concurrent_db)
events = db_check.get_all_events()
print(f"Events in DB: {len(events)}")
print(f"Sequences: {[e['sequence'] for e in events]}")
db_check.close()

if os.path.exists(concurrent_db):
    os.remove(concurrent_db)
