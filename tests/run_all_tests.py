#!/usr/bin/env python3
"""
tests/run_all_tests.py
Master test runner for the Torchlight pt-BR translation and installer test suite.
Discovers and executes Tiers 1-4, reports comprehensive test statistics,
and exits with code 0 on 100% pass, or non-zero on any failure.
"""

import sys
import os
import time
import argparse
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Color terminal formatting
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


TIER_CONFIG = {
    1: {
        "name": "Tier 1: Feature Coverage (F01–F16)",
        "dir": "tier1_feature_coverage",
        "pattern": "test_*.py"
    },
    2: {
        "name": "Tier 2: Boundary & Corner Cases",
        "dir": "tier2_boundary_corner",
        "pattern": "test_*.py"
    },
    3: {
        "name": "Tier 3: Cross-Feature Integration",
        "dir": "tier3_cross_feature",
        "pattern": "test_*.py"
    },
    4: {
        "name": "Tier 4: Realistic Game Workloads",
        "dir": "tier4_real_world",
        "pattern": "test_*.py"
    }
}


class TierTestResult:
    def __init__(self, tier_num, tier_name):
        self.tier_num = tier_num
        self.tier_name = tier_name
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0
        self.duration = 0.0
        self.failure_details = []


def run_tier(tier_num, verbose=False):
    config = TIER_CONFIG[tier_num]
    tier_dir = PROJECT_ROOT / "tests" / config["dir"]
    result = TierTestResult(tier_num, config["name"])
    
    if not tier_dir.exists():
        print(f"{COLOR_YELLOW}[WARN] Directory {tier_dir} does not exist.{COLOR_RESET}")
        return result

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(tier_dir), pattern=config["pattern"])
    
    start_time = time.time()
    
    # Custom runner with capture
    stream = sys.stdout if verbose else None
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(stream=stream, verbosity=verbosity)
    test_result = runner.run(suite)
    
    result.duration = time.time() - start_time
    result.total = test_result.testsRun
    result.failed = len(test_result.failures)
    result.errors = len(test_result.errors)
    result.skipped = len(test_result.skipped)
    result.passed = result.total - (result.failed + result.errors + result.skipped)
    
    for test, err in test_result.failures:
        result.failure_details.append(("FAIL", str(test), err))
    for test, err in test_result.errors:
        result.failure_details.append(("ERROR", str(test), err))
        
    return result


def main():
    parser = argparse.ArgumentParser(description="Torchlight pt-BR E2E Master Test Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run a specific tier only")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose test execution output")
    args = parser.parse_args()

    selected_tiers = [args.tier] if args.tier else [1, 2, 3, 4]

    print("=" * 80)
    print(f"{COLOR_BOLD}{COLOR_CYAN} Torchlight pt-BR — E2E Test Suite Master Runner{COLOR_RESET}")
    print("=" * 80)
    print(f"Working Directory : {PROJECT_ROOT}")
    print(f"Executing Tiers   : {', '.join(str(t) for t in selected_tiers)}")
    print(f"Python Runtime    : {sys.version.split()[0]}")
    print("=" * 80)
    print()

    tier_results = []
    total_start = time.time()

    for tier_num in selected_tiers:
        name = TIER_CONFIG[tier_num]["name"]
        print(f"--> Executing {COLOR_BOLD}{name}{COLOR_RESET}...")
        res = run_tier(tier_num, verbose=args.verbose)
        tier_results.append(res)
        
        status_col = COLOR_GREEN if (res.failed == 0 and res.errors == 0) else COLOR_RED
        status_str = "PASS" if (res.failed == 0 and res.errors == 0) else "FAIL"
        print(f"    {status_col}[{status_str}]{COLOR_RESET} Tests: {res.total} | Passed: {res.passed} | Failed: {res.failed} | Errors: {res.errors} ({res.duration:.3f}s)")
        print()

    total_duration = time.time() - total_start

    # Summary Table
    print("=" * 80)
    print(f"{COLOR_BOLD} TEST EXECUTION SUMMARY TABLE{COLOR_RESET}")
    print("=" * 80)
    print(f"{'Tier':<6} | {'Name':<36} | {'Total':<6} | {'Pass':<6} | {'Fail':<6} | {'Time':<8} | {'Status':<6}")
    print("-" * 80)

    grand_total = 0
    grand_passed = 0
    grand_failed = 0
    grand_errors = 0

    for r in tier_results:
        grand_total += r.total
        grand_passed += r.passed
        grand_failed += r.failed
        grand_errors += r.errors

        status_text = "PASS" if (r.failed == 0 and r.errors == 0) else "FAIL"
        color = COLOR_GREEN if status_text == "PASS" else COLOR_RED
        print(f"{r.tier_num:<6} | {r.tier_name:<36} | {r.total:<6} | {r.passed:<6} | {r.failed:<6} | {r.duration:>6.3f}s | {color}{status_text:<6}{COLOR_RESET}")

    print("-" * 80)
    final_status = "PASS" if (grand_failed == 0 and grand_errors == 0 and grand_total > 0) else "FAIL"
    final_color = COLOR_GREEN if final_status == "PASS" else COLOR_RED
    print(f"{'TOTAL':<6} | {'All Executed Test Suites':<36} | {grand_total:<6} | {grand_passed:<6} | {grand_failed:<6} | {total_duration:>6.3f}s | {final_color}{COLOR_BOLD}{final_status:<6}{COLOR_RESET}")
    print("=" * 80)

    # Print failure details if any
    any_failures = False
    for r in tier_results:
        if r.failure_details:
            any_failures = True
            print(f"\n{COLOR_RED}[FAILURES IN {r.tier_name}]{COLOR_RESET}")
            for tag, test_name, trace in r.failure_details:
                print(f"--- {tag}: {test_name} ---")
                print(trace)
                print()

    if final_status == "PASS":
        print(f"\n{COLOR_GREEN}{COLOR_BOLD}>>> SUCCESS: 100% of all {grand_total} test cases passed successfully! <<<{COLOR_RESET}\n")
        return 0
    else:
        print(f"\n{COLOR_RED}{COLOR_BOLD}>>> FAILURE: Test suite failed with {grand_failed} failure(s) and {grand_errors} error(s)! <<<{COLOR_RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
