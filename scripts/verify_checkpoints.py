import os
import subprocess
import sys

# Reconfigure stdout/stderr to support UTF-8 characters like arrow symbols in Windows console
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def run_command(cmd, env=None, cwd=None):
    print(f"\nRunning: {cmd}")
    # Merge with current env
    current_env = os.environ.copy()
    if env:
        current_env.update(env)
    
    # Run the command
    result = subprocess.run(cmd, env=current_env, cwd=cwd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return result

def main():
    print("=" * 80)
    print("PARIKSHAK SYSTEM INTEGRITY & CHECKPOINT VERIFIER")
    print("=" * 80)
    
    # Clean previous generated run artifacts to get a clean Git status
    subprocess.run("git checkout -- adversarial_constitutional_review_report.md constitutional_runtime_proof_packet.md review_packets/ storage/", shell=True, capture_output=True)
    
    # 1. Verify git repo is up-to-date with parikshak/main
    print("\n[STEP 1] Git Repository Verification")
    
    # Fetch latest parikshak changes
    run_command("git fetch parikshak")
    
    # Get current branch
    branch_res = run_command("git rev-parse --abbrev-ref HEAD")
    current_branch = branch_res.stdout.strip()
    print(f"  Current Branch: {current_branch}")
    
    # Get local commit hash
    local_hash_res = run_command("git rev-parse HEAD")
    local_hash = local_hash_res.stdout.strip()
    
    # Get remote commit hash for parikshak/main
    remote_hash_res = run_command("git rev-parse parikshak/main")
    remote_hash = remote_hash_res.stdout.strip()
    
    print(f"  Local commit:  {local_hash}")
    print(f"  Remote commit: {remote_hash}")
    
    git_up_to_date = (local_hash == remote_hash)
    if git_up_to_date:
        print("  Status: UP-TO-DATE with parikshak/main (OK)")
    else:
        print("  Status: DIVERGED from parikshak/main (Divergence or pending updates)")
        
    # Check working directory status (ignoring untracked files with -uno)
    status_res = run_command("git status --porcelain -uno")
    uncommitted = status_res.stdout.strip()
    if not uncommitted:
        print("  Tracked files status: CLEAN")
    else:
        print("  Tracked files status: UNCOMMITTED CHANGES PRESENT:")
        print(f"    {uncommitted.replace(chr(10), chr(10) + '    ')}")

    # 2. Checkpoint Loop
    print("\n[STEP 2] Executing Verification Checkpoints")
    
    checkpoints = [
        {
            "name": "Audit Checks (audit_checks.py)",
            "command": "python audit_checks.py",
            "env": {}
        },
        {
            "name": "Constitutional Review (run_constitutional_review_tests.py)",
            "command": "python scripts/run_constitutional_review_tests.py",
            "env": {"PYTHONPATH": "."}
        },
        {
            "name": "Master Operational Validation (run_operational_validation.py)",
            "command": "python tests/run_operational_validation.py",
            "env": {}
        },
        {
            "name": "Determinism Proof (test_determinism_proof.py)",
            "command": "python tests/test_determinism_proof.py",
            "env": {"PYTHONPATH": "."}
        },
        {
            "name": "Pytest Test Suite (pytest)",
            "command": "python -m pytest",
            "env": {"PYTHONPATH": "."}
        }
    ]
    
    results = []
    
    for cp in checkpoints:
        print(f"\n--- Running Checkpoint: {cp['name']} ---")
        env_vars = cp.get("env", {})
        env_vars["PYTHONIOENCODING"] = "utf-8"
        res = run_command(cp["command"], env=env_vars)
        
        success = (res.returncode == 0)
        status = "PASS" if success else "FAIL"
        
        # Print output preview
        print(f"  Exit code: {res.returncode}")
        if res.stdout:
            stdout_lines = res.stdout.strip().split("\n")
            print("  Stdout preview:")
            for line in stdout_lines[-10:]: # print last 10 lines
                print(f"    {line}")
        if res.stderr:
            stderr_lines = res.stderr.strip().split("\n")
            print("  Stderr preview:")
            for line in stderr_lines[-10:]:
                print(f"    {line}")
                
        results.append({
            "name": cp["name"],
            "status": status,
            "exit_code": res.returncode
        })
        
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Git Up-To-Date: {'PASS' if git_up_to_date else 'FAIL'}")
    
    all_passed = git_up_to_date
    for r in results:
        print(f"Checkpoint: {r['name']:<60} | Status: {r['status']} (Exit Code: {r['exit_code']})")
        if r['status'] == "FAIL":
            all_passed = False
            
    print("-" * 80)
    if all_passed:
        print("FINAL VERIFICATION VERDICT: SUCCESS (System is correct and up to date!)")
        sys.exit(0)
    else:
        print("FINAL VERIFICATION VERDICT: FAILED (Some checks failed or repo is out of date)")
        sys.exit(1)

if __name__ == "__main__":
    main()
