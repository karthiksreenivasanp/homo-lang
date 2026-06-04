import random
import subprocess

for i in range(100):

    with open("temp.homo", "w") as f:

        f.write(f"""
set a as {random.randint(1,100)}
set b as {random.randint(1,100)}

calculate c as a + b

show c
""")

    subprocess.run(
        ["python3", "main.py", "temp.homo"]
    )

print("Fuzz Test Complete")
