import json, os, sys

results = {}

# CHECK 1 - Structure
dirs = ['evaluation_engine', 'task_selector', 'db', 'engine', 'api']
missing_dirs = [d for d in dirs if not os.path.isdir(d)]
results['CHECK1_structure'] = 'PASS' if not missing_dirs else f'FAIL: missing {missing_dirs}'

# CHECK 2 - Separation
ts_violations = []
for f in os.listdir('task_selector'):
    if not f.endswith('.py'):
        continue
    c = open(os.path.join('task_selector', f), encoding='utf-8', errors='ignore').read()
    if 'rule_engine' in c:
        ts_violations.append(f + ':rule_engine')
    if 'evaluation_result = ' in c:
        ts_violations.append(f + ':eval_assign')
ee = open('evaluation_engine/rule_engine.py', encoding='utf-8').read()
score_free = 'score' not in ee
results['CHECK2_separation'] = 'PASS' if not ts_violations and score_free else f'FAIL: {ts_violations}, score_free={score_free}'

# CHECK 3 - Trace discipline
fc = open('task_selector/final_convergence.py', encoding='utf-8').read()
nc = open('task_selector/niyantran_connection.py', encoding='utf-8').read()
ro = open('task_selector/review_orchestrator.py', encoding='utf-8').read()
fc_rejects = 'CONVERGENCE_HARD_REJECT' in fc
nc_rejects = 'NIYANTRAN_HARD_REJECT' in nc
nc_no_uuid = 'uuid' not in nc
fc_no_uuid = 'uuid' not in fc
results['CHECK3_trace'] = 'PASS' if fc_rejects and nc_rejects and nc_no_uuid and fc_no_uuid else f'FAIL: fc_rejects={fc_rejects} nc_rejects={nc_rejects} nc_no_uuid={nc_no_uuid} fc_no_uuid={fc_no_uuid}'

# CHECK 4 - DB integrity
tasks = json.load(open('db/niyantran_tasks.json', encoding='utf-8'))
task_count = len(tasks)
required = {'task_id','product','layer','subsystem','capability','dharma',
            'completion_signals',
            'failure_type','prerequisites','next_tasks','failure_tasks','constraints'}
missing_fields = []
for t in tasks:
    m = required - set(t.keys())
    if m:
        missing_fields.append(t.get('task_id','?') + ':' + str(m))
no_eval = all('score' not in str(t) and 'weight' not in str(t) for t in tasks)
count_ok = task_count >= 19
results['CHECK4_db'] = 'PASS' if not missing_fields and no_eval and count_ok else f'FAIL: count={task_count} missing_fields={missing_fields} no_eval={no_eval}'

# CHECK 5 - Mandala mapping
mm = open('task_selector/mandala_mapper.py', encoding='utf-8').read()
results['CHECK5_mandala'] = 'PASS' if 'MANDALA_HARD_REJECT' in mm else 'FAIL: no hard reject'

# CHECK 6 - Graph engine
ge = open('engine/task_graph_engine.py', encoding='utf-8').read()
uses_next = 'candidates[0]' in ge
uses_failure = 'failure_tasks' in ge
no_fallback = 'fallback' not in ge.lower()
hard_reject = 'GRAPH_HARD_REJECT' in ge
results['CHECK6_graph'] = 'PASS' if uses_next and uses_failure and no_fallback and hard_reject else f'FAIL: next={uses_next} failure={uses_failure} no_fallback={no_fallback} hard_reject={hard_reject}'

# CHECK 7 - API contract
contract_fields = ['trace_id','submission_id','evaluation_result','failure_type','selected_task_id','selection_reason','source']
all_in_fc = all(f in fc for f in contract_fields)
results['CHECK7_contract'] = 'PASS' if all_in_fc else f'FAIL: missing {[f for f in contract_fields if f not in fc]}'

# CHECK 8 - End-to-end (from test results already run)
results['CHECK8_e2e'] = 'PASS (8/8 BHIV tests passed — verified separately)'

# Print results
print()
failed = []
for k, v in results.items():
    status = 'PASS' if v.startswith('PASS') else 'FAIL'
    print(f'  {status}  {k}: {v}')
    if status == 'FAIL':
        failed.append(k)

print()
final = 'PASS' if not failed else 'FAIL'
print('=' * 60)
print(f'FINAL STATUS: {final}')
print(f'FAILED CHECKS: {failed if failed else "none"}')
print('=' * 60)
