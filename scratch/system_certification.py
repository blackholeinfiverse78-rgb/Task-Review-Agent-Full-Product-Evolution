import subprocess
import sys
import os

def run_certification():
    print("STARTING SYSTEM CERTIFICATION...")
    
    script_path = "tests/test_dfa_validation.py"
    cmd = [sys.executable, script_path]
    
    outputs = []
    for i in range(3):
        print(f"RUN {i+1}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"CERTIFICATION STATUS: FAILED")
            print(f"Failure Point: Run {i+1} failed with exit code {result.returncode}")
            print(result.stderr)
            return

        # Capture normalized output (removing timing variations if any)
        # The DFA_VALIDATION_REPORT should be stable
        output = result.stdout.strip()
        outputs.append(output)
    
    # Verify exact string match across runs
    if len(set(outputs)) != 1:
        print("CERTIFICATION STATUS: FAILED")
        print("Failure Point: Non-reproducible output across runs.")
        return

    final_output = outputs[0]
    print("\nFINAL OUTPUT CAPTURED:")
    print("-" * 50)
    print(final_output)
    print("-" * 50)

    # Verify DFA_VALIDATION_REPORT format and PASS status
    required_lines = [
        "Graph Integrity: PASS",
        "State Exhaustiveness: PASS",
        "Input Safety: PASS",
        "Execution Purity: PASS",
        "Determinism: PASS",
        "Boundary Contract: PASS",
        "FINAL STATUS: TRUE 10/10",
        "TANTRA STATUS: FULLY COMPLIANT"
    ]
    
    missing = [line for line in required_lines if line not in final_output]
    if missing:
        print("CERTIFICATION STATUS: FAILED")
        print(f"Failure Point: Missing or incorrect validation fields: {missing}")
        return

    print("\nCERTIFICATION STATUS: VERIFIED")
    print("REPRODUCIBILITY: CONFIRMED")
    print("SYSTEM STATUS: TRUE 10/10")

if __name__ == "__main__":
    run_certification()
