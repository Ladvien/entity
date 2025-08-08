#!/usr/bin/env python3
"""Complete validation suite for CLI-generated examples."""

import subprocess
import sys
from pathlib import Path


def run_test_suite(test_file: str, description: str) -> bool:
    """Run a test suite and return success status."""
    print(f"\n🚀 {description}")
    print("=" * 60)

    try:
        result = subprocess.run(
            [sys.executable, test_file], capture_output=False, text=True
        )

        return result.returncode == 0
    except Exception as e:
        print(f"💥 Error running {test_file}: {e}")
        return False


def main():
    """Run all validation tests for CLI-generated examples."""
    print("🧪 Entity CLI Examples - Complete Validation Suite")
    print("=" * 70)
    print("This suite validates that the CLI `entity init` command generates")
    print("working, idiomatic examples that follow Entity framework patterns.")
    print("=" * 70)

    # Test suites to run
    test_suites = [
        ("test_examples_standalone.py", "Generated Examples Structure & Content"),
        ("test_compilation_check.py", "Python Compilation & YAML Validation"),
        ("test_direct_cli.py", "CLI Functionality Integration"),
    ]

    results = []

    for test_file, description in test_suites:
        if Path(test_file).exists():
            success = run_test_suite(test_file, description)
            results.append((description, success))
        else:
            print(f"⚠️ Test file {test_file} not found, skipping...")
            results.append((description, False))

    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL VALIDATION RESULTS")
    print("=" * 70)

    passed = 0
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {description}")
        if success:
            passed += 1

    success_rate = (passed / total) * 100 if total > 0 else 0

    print("=" * 70)
    print(
        f"🎯 Overall Results: {passed}/{total} test suites passed ({success_rate:.1f}%)"
    )

    if passed == total:
        print("\n🎉 SUCCESS! All validation tests passed!")
        print("   • CLI-generated examples are syntactically correct")
        print("   • Generated projects follow Entity framework patterns")
        print("   • Examples include proper error handling and documentation")
        print("   • Workflow configurations are valid and use real plugins")
        print("   • Test files are properly structured for pytest")
        print("\n✨ The `entity init` command is ready for production use!")
        return True
    else:
        print(f"\n💥 FAILURE: {total - passed} test suite(s) failed")
        print("   Generated examples may have issues that need addressing.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
