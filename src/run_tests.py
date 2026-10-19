
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent
PYTHON = sys.executable

TEST_FILES = [
    "test_sql_security.py",
    "test_sql_intent.py",
    "test_sql_agent.py",
]


def main():
    for test_file in TEST_FILES:
        test_path = SRC_DIR / test_file

        print(f"\n{'=' * 55}", flush=True)
        print(f"Running: {test_path.name}", flush=True)
        print("=" * 55, flush=True)

        result = subprocess.run(
            [PYTHON, str(test_path)],
            cwd=PROJECT_DIR,
            check=False,
        )

        if result.returncode != 0:
            print(f"\nFAILED: {test_file}", flush=True)
            sys.exit(result.returncode)

    print(f"\n{'=' * 55}", flush=True)
    print("ALL TEST SUITES PASSED", flush=True)
    print("=" * 55, flush=True)


if __name__ == "__main__":
    main()
