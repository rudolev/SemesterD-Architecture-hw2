#!/usr/bin/env python3
import subprocess
import math

# ANSI escape color sequences
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Test data format: (base, number, epsilon, expect_error_or_usage)
tests = [
    # --- PDF Provided Tests ---
    ("10", "2", "1e-17", False),
    ("10", "3", "1e-17", False),
    ("2", "8", "1e-17", False),
    ("8", "4", "1e-17", False),
    ("10", "7", "0.1", False),
    ("10", "7", "0.01", False),
    ("10", "7", "0.001", False),
    ("10", "7", "0.0001", False),
    ("10", "7", "0.00001", False),
    ("10", "7", "1e-5", False),
    ("10", "7", "1e-10", False),
    ("10", "7", "1e-15", False),
    ("10", "7", "1e-17", False),
    
    # --- Edge Cases & Argument Validation Tests ---
    ("shalom", "rav", "shuvech", True), # Wrong arguments
    ("1", "2", None, True),             # Too few arguments
    ("2", "3", "4 5", True),            # Too many arguments
    
    # --- Additional Functional Verification ---
    ("2", "1024", "1e-17", False),      # Exact higher power of 2
    ("3", "27", "1e-17", False),        # Exact power of 3
    ("16", "2", "1e-17", False),        # Fractions fractional log base > number
    ("5", "125", "1e-15", False)
]

def run_program(args):
    """Executes the discrete log binary with given string arguments."""
    cmd = ["./disc-log"] + [str(a) for a in args if a is not None]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def verify_output(base, num, output):
    """Validates if the output string closely matches the correct analytical evaluation."""
    try:
        # Expected output format line structural format: log_(10)(2) = 0.301...
        parts = output.split("=")
        if len(parts) != 2:
            return False
        
        parsed_val = float(parts[1].strip())
        actual_val = math.log(float(num), float(base))
        
        # Check tolerance relative convergence
        return math.isclose(parsed_val, actual_val, rel_tol=1e-5, abs_tol=1e-5)
    except Exception:
        return False

def main():
    # Enforce compilation state check first
    subprocess.run(["make", "clean"], capture_output=True)
    make_proc = subprocess.run(["make"], capture_output=True, text=True)
    if make_proc.returncode != 0:
        print(f"{RED}Compilation failed via Makefile:{RESET}\n{make_proc.stderr}")
        return

    passed_count = 0

    for i, test in enumerate(tests, 1):
        base, num, eps, expect_err = test
        args = [base, num, eps] if eps is not None else [base, num]
        if len(args) == 3 and " " in str(eps): # Handle the too many arguments edge test split explicitly
            args = [base, num] + eps.split()

        ret_code, stdout, stderr = run_program(args)

        if expect_err:
            # Errors must report a returncode != 0 and content printed safely to stderr
            if ret_code != 0 and "Usage:" in stderr:
                print(f"Test {i}: {GREEN}PASS{RESET} (Gracefully caught invalid input context)")
                passed_count += 1
            else:
                print(f"Test {i}: {RED}FAIL{RESET} (Expected application error interface to stderr)")
        else:
            if ret_code == 0 and verify_output(base, num, stdout):
                print(f"Test {i} (log_{base}({num})): {GREEN}PASS{RESET}")
                passed_count += 1
            else:
                print(f"Test {i} (log_{base}({num})): {RED}FAIL{RESET} -> Got output: '{stdout}'")

    print("\n-----------------------------------------")
    print(f"Final Verification Matrix: {passed_count}/{len(tests)} tests passed successfully.")

if __name__ == "__main__":
    main()