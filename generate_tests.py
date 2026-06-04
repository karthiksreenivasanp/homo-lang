import os
import subprocess

os.makedirs("tests", exist_ok=True)

tests = {
    "variables.homo": '''
show "Variables Test"

set name as "Karthik"
set age as 20

show name
show age
''',

    "math.homo": '''
show "Math Test"

calculate result as 10 + 20 * 3

show result
''',

    "if.homo": '''
show "If Test"

set age as 18

if age >= 18
    show "Adult"
otherwise
    show "Minor"
''',

    "repeat.homo": '''
show "Repeat Test"

repeat 5

    show "Hello"
''',

    "while.homo": '''
show "While Test"

set i as 1

while i <= 5

    show i

    calculate i as i + 1
''',

    "for.homo": '''
show "For Test"

set nums as [1,2,3,4,5]

for n in nums

    show n
''',

    "function.homo": '''
define greet name

    show "Hello"
    show name

call greet "Karthik"
''',

    "return.homo": '''
define add a b

    return a + b

set result as call add 5 7

show result
''',

    "lists.homo": '''
set names as ["A","B","C"]

append "D" to names

show names
''',

    "input.homo": '''
ask "Your Name:" name

show "Hello"

show name
''',

    "website.homo": '''
make website

set theme as dark

add header "My Portfolio"

add card "About"

    AI Developer

add footer "Made with Homo"

publish website
''',

    "stress.homo": '''
repeat 10000

    calculate x as 1 + 1

show "Done"
'''
}

for filename, content in tests.items():
    with open(os.path.join("tests", filename), "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Created {len(tests)} test files in ./tests")

print("\nRunning tests...\n")

for filename in sorted(os.listdir("tests")):
    if filename.endswith(".homo"):
        print("=" * 60)
        print("RUNNING:", filename)
        print("=" * 60)

        subprocess.run(
            ["python3", "main.py", os.path.join("tests", filename)],
            check=False
        )

        print()
