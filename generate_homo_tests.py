import os

os.makedirs("tests", exist_ok=True)

tests = {
"test_show.homo": '''
show "Hello World"
''',

"test_set.homo": '''
set name as "Karthi"
show name
''',

"test_function.homo": '''
define greet person
    show person

call greet "Karthi"
''',

"test_loop.homo": '''
repeat 5
    show "Hi"
''',

"test_list.homo": '''
set items as ["A","B","C"]
show items[0]
append "D" to items
show items
''',

"test_file.homo": '''
write sample.txt as "Hello Homo"
read sample.txt
show content
''',

"test_http.homo": '''
fetch https://jsonplaceholder.typicode.com/todos/1 as response
show response
''',

"test_database.homo": '''
open database test
save username as "Karthi"
show "Database Test Complete"
''',

"test_recursion.homo": '''
define countdown n

    show n

    if n > 1

        call countdown n - 1

call countdown 5
''',

"test_stress.homo": '''
set total as 0

repeat 1000

    calculate total as total + 1

show total
'''
}

for name, content in tests.items():
    with open(f"tests/{name}", "w") as f:
        f.write(content.strip())

print("Created", len(tests), "test files")
