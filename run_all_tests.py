import os
import subprocess

passed = 0
failed = 0

for test in sorted(os.listdir("tests")):

    if not test.endswith(".homo"):
        continue

    print("\n" + "="*60)
    print("RUNNING:", test)
    print("="*60)

    result = subprocess.run(
        ["python3", "main.py", f"tests/{test}"]
    )

    if result.returncode == 0:
        passed += 1
    else:
        failed += 1

print("\n")
print("="*60)
print("PASSED:", passed)
print("FAILED:", failed)
print("="*60)
