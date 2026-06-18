#!/usr/bin/env python3
import subprocess
import math

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

tests = [
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
    ("shalom", "rav", "shuvech", True), 
    ("1", "2", None, True),             
    ("2", "3", "4 5", True),            
    ("2", "1024", "1e-17", False),      
    ("3", "27", "1e-17", False),        
    ("16", "2", "1e-17", False),        
    ("5", "125", "1e-15", False)
]

def run_program(args):
    cmd = ["./disc-log"] + [str(a) for a in args if a is not None]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def verify_output(base, num, output):
    try:
        parts = output.split("=")
        if len(parts) != 2:
            return False
        parsed_val = float(parts[1].strip())
        actual_val = math.log(float(num), float(base))
        return math.isclose(parsed_val, actual_val, rel_tol=1e-2, abs_tol=1e-2)
    except Exception:
        return False

def get_precision_places(eps_str):
    """Calculates precision decimal places based on epsilon input string."""
    if eps_str is None:
        return 4
    try:
        val = float(eps_str)
        # For small scientific notation numbers (e.g., 1e-17), cap presentation precision
        if 'e' in eps_str.lower() or val < 1e-4:
            # Look at scientific notation or default to a clean max value
            if 'e' in eps_str.lower():
                exponent = abs(int(eps_str.lower().split('e')[1]))
                return min(exponent, 16) # cap at 16 digits to keep string clean
            return 5
        # For standard decimal strings (e.g., 0.001), count the decimal places
        if '.' in eps_str:
            return len(eps_str.split('.')[1])
        return 4
    except ValueError:
        return 4

def main():
    subprocess.run(["make", "clean"], capture_output=True)
    make_proc = subprocess.run(["make"], capture_output=True, text=True)
    if make_proc.returncode != 0:
        print(f"{RED}Compilation failed via Makefile:{RESET}\n{make_proc.stderr}")
        return

    passed_count = 0
    results_raw = []

    # 1. Gather data and evaluate precision
    for i, test in enumerate(tests, 1):
        base, num, eps, expect_err = test
        args = [base, num, eps] if eps is not None else [base, num]
        if len(args) == 3 and " " in str(eps):
            args = [base, num] + eps.split()

        ret_code, stdout, stderr = run_program(args)
        inputs_str = f"base={base}, num={num}, eps={eps}"
        
        if expect_err:
            expected = "Error (Usage)"
            if ret_code != 0 and "Usage:" in stderr:
                actual = "Error (Usage)"
                status = f"{GREEN}PASS{RESET}"
                passed_count += 1
            else:
                actual = f"Code {ret_code}: {stdout or stderr}"
                status = f"{RED}FAIL{RESET}"
        else:
            try:
                # Dynamically set precision to match the epsilon scale
                precision = get_precision_places(eps)
                raw_log = math.log(float(num), float(base))
                
                # Check if it represents an exact integer value (like 3 or 10)
                if raw_log.is_integer() and precision <= 4:
                    expected = f"log_{base}({num}) = {int(raw_log)}"
                else:
                    expected = f"log_{base}({num}) = {raw_log:.{precision}f}"
            except Exception:
                expected = "Valid Float Output"

            if ret_code == 0 and verify_output(base, num, stdout):
                actual = stdout
                status = f"{GREEN}PASS{RESET}"
                passed_count += 1
            else:
                actual = stdout if stdout else f"Err Code {ret_code}: {stderr}"
                status = f"{RED}FAIL{RESET}"
        
        results_raw.append((str(i), inputs_str, expected, actual, status))

    # 2. Dynamically calculate the ideal column widths (including headers)
    headers = ["ID", "Test Inputs", "Expected Output", "Actual Output", "Status"]
    
    col_widths = [
        max(len(row[0]) for row in results_raw) if results_raw else 0,
        max(len(row[1]) for row in results_raw) if results_raw else 0,
        max(len(row[2]) for row in results_raw) if results_raw else 0,
        max(len(row[3]) for row in results_raw) if results_raw else 0,
        4 # Baseline width for "Status" word length
    ]
    col_widths = [max(w, len(h)) for w, h in zip(col_widths, headers)]

    # 3. Dynamic layout structures
    row_format = "│ {:<{}} │ {:<{}} │ {:<{}} │ {:<{}} │ {:<{}} │"
    top_format = "┌─" + "─┬─".join(["{:<{}}"] * 5) + "─┐"
    sep_format = "├─" + "─┼─".join(["{:<{}}"] * 5) + "─┤"
    bot_format = "└─" + "─┴─".join(["{:<{}}"] * 5) + "─┘"

    f0, f1, f2, f3, f4 = ["─"*w for w in col_widths]

    # 4. Print Beautifully Aligned Table
    print("\n" + top_format.format(f0, col_widths[0], f1, col_widths[1], f2, col_widths[2], f3, col_widths[3], f4, col_widths[4]))
    print(row_format.format(headers[0], col_widths[0], headers[1], col_widths[1], headers[2], col_widths[2], headers[3], col_widths[3], headers[4], col_widths[4]))
    print(sep_format.format(f0, col_widths[0], f1, col_widths[1], f2, col_widths[2], f3, col_widths[3], f4, col_widths[4]))
    
    for row in results_raw:
        # Pad formatting width safely past hidden ANSI color control bytes
        status_width = col_widths[4] + 9 if (GREEN in row[4] or RED in row[4]) else col_widths[4]
        print(row_format.format(row[0], col_widths[0], row[1], col_widths[1], row[2], col_widths[2], row[3], col_widths[3], row[4], status_width))

    print(bot_format.format(f0, col_widths[0], f1, col_widths[1], f2, col_widths[2], f3, col_widths[3], f4, col_widths[4]))

    final_color = GREEN if passed_count == len(tests) else RED
    print(f"\nFinal Verification Matrix: {final_color}{passed_count}/{len(tests)} tests passed successfully.{RESET}\n")

if __name__ == "__main__":
    main()