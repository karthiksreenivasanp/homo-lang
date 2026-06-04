import os
import subprocess

passed = 0
failed = 0

for file in sorted(os.listdir("tests")):

    if file.endswith(".homo"):

        print(f"\nRunning {file}")

        result = subprocess.run(
            ["python3", "main.py", f"tests/{file}"]
        )

        if result.returncode == 0:
            passed += 1
        else:
            failed += 1

print("\n===================")
print("Passed:", passed)
print("Failed:", failed)
print("===================")


