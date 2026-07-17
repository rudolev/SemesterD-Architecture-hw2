#!/usr/bin/env python3
import subprocess

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Hardcoded test configurations based on your algorithm's expected output ("exp")
# Format: (base, num, eps, expected_string_value, expect_err)
tests = [
    # --- published ---
    ("10", "2", "1e-17", "0.301029995663981195", False),
    ("10", "3", "1e-17", "0.477121254719662437", False),
    ("8", "4", "1e-17", "0.666666666666666667", False),
    ("10", "7", "0.1", "0.846153846153846154", False),
    ("10", "7", "0.01", "0.845070422535211268", False),
    ("10", "7", "0.001", "0.845098039215686275", False),
    ("10", "7", "1e-05", "0.845098039215686275", False),
    ("10", "7", "1e-10", "0.845098040014256831", False),
    ("10", "7", "1e-17", "0.845098040014256831", False),

    # --- reciprocal ---
    ("27", "3", "1e-17", "0.333333333333333333", False),
    ("8", "4", "1e-17", "0.666666666666666667", False),
    ("1000", "10", "1e-17", "0.333333333333333333", False),
    ("10", "5", "1e-17", "0.698970004336018805", False),

    # --- irrational ---
    ("2", "3", "1e-17", "1.58496250072115618", False),
    ("3", "7", "1e-15", "1.77124374916142226", False),
    ("7", "3", "1e-15", "0.564575034053579614", False),
    ("5", "11", "1e-15", "1.48989610240497807", False),
    ("2", "7", "1e-15", "2.80735492205760411", False),

    # --- eps_sensitive ---
    ("3", "7", "0.01", "1.77142857142857143", False),
    ("3", "7", "0.001", "1.77124183006535948", False),
    ("2", "5", "0.1", "2.33333333333333333", False),
    ("2", "5", "0.001", "2.32192846034214619", False),
    ("5", "2", "0.01", "0.430769230769230769", False),

    # --- fractional ---
    ("2.5", "9.4", "1e-15", "2.44541346030301342", False),
    ("1.2", "3.7", "1e-15", "7.17596340584538131", False),

    # --- large ---
    ("2", "1000000", "1e-15", "19.9315685693241741", False),
    ("10", "123456", "1e-15", "5.09151220162777168", False),

    # --- near_one ---
    ("1.1", "5", "1e-10", "16.8863170307550864", False),
    ("1.05", "3", "1e-10", "22.517085305411042", False),

    # --- error handling validation ---
    ("shalom", "rav", "shuvech", None, True), 
    ("1", "2", None, None, True),             
    ("2", "3", "4 5", None, True)
]

def run_program(args):
    cmd = ["./disc-log"] + [str(a) for a in args if a is not None]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def verify_output(stdout, exp_val):
    if not stdout:
        return False
    try:
        parts = stdout.split("=")
        if len(parts) != 2:
            return False
        # Extract the value on the right side of the equals sign
        got_str = parts[1].strip()
        
        # Enforce a strict string comparison to prevent IEEE 754 float conversion rounding
        return got_str == exp_val
    except Exception:
        return False

def main():
    subprocess.run(["make", "clean"], capture_output=True)
    make_proc = subprocess.run(["make"], capture_output=True, text=True)
    if make_proc.returncode != 0:
        print(f"{RED}Compilation failed via Makefile:{RESET}\n{make_proc.stderr}")
        return

    passed_count = 0
    results_raw = []

    for i, test in enumerate(tests, 1):
        base, num, eps, exp_val, expect_err = test
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
            expected = f"log_{base}({num}) = {exp_val}"
            
            if ret_code == 0 and verify_output(stdout, exp_val):
                actual = stdout
                status = f"{GREEN}PASS{RESET}"
                passed_count += 1
            else:
                actual = stdout if stdout else f"Err Code {ret_code}: {stderr}"
                status = f"{RED}FAIL{RESET}"
        
        results_raw.append((str(i), inputs_str, expected, actual, status))

    headers = ["ID", "Test Inputs", "Expected Output", "Actual Output", "Status"]
    
    col_widths = [
        max(len(row[0]) for row in results_raw) if results_raw else 0,
        max(len(row[1]) for row in results_raw) if results_raw else 0,
        max(len(row[2]) for row in results_raw) if results_raw else 0,
        max(len(row[3]) for row in results_raw) if results_raw else 0,
        4 
    ]
    col_widths = [max(w, len(h)) for w, h in zip(col_widths, headers)]

    row_format = "│ {:<{}} │ {:<{}} │ {:<{}} │ {:<{}} │ {:<{}} │"
    top_format = "┌─" + "─┬─".join(["{:<{}}"] * 5) + "─┐"
    sep_format = "├─" + "─┼─".join(["{:<{}}"] * 5) + "─┤"
    bot_format = "└─" + "─┴─".join(["{:<{}}"] * 5) + "─┘"

    f0, f1, f2, f3, f4 = ["─"*w for w in col_widths]

    print("\n" + top_format.format(f0, col_widths[0], f1, col_widths[1], f2, col_widths[2], f3, col_widths[3], f4, col_widths[4]))
    print(row_format.format(headers[0], col_widths[0], headers[1], col_widths[1], headers[2], col_widths[2], headers[3], col_widths[3], headers[4], col_widths[4]))
    print(sep_format.format(f0, col_widths[0], f1, col_widths[1], f2, col_widths[2], f3, col_widths[3], f4, col_widths[4]))
    
    for row in results_raw:
        status_width = col_widths[4] + 9 if (GREEN in row[4] or RED in row[4]) else col_widths[4]
        print(row_format.format(row[0], col_widths[0], row[1], col_widths[1], row[2], col_widths[2], row[3], col_widths[3], row[4], status_width))

    print(bot_format.format(f0, col_widths[0], f1, col_widths[1], f2, col_widths[2], f3, col_widths[3], f4, col_widths[4]))

    final_color = GREEN if passed_count == len(tests) else RED
    print(f"\nFinal Verification Matrix: {final_color}{passed_count}/{len(tests)} tests passed successfully.{RESET}\n")

if __name__ == "__main__":
    main()