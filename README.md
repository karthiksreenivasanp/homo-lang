# Homo Language - Local Run Guide

[![Build Status](https://github.com/karthiksreenivasanp/homo-lang/actions/workflows/test.yml/badge.svg)](https://github.com/karthiksreenivasanp/homo-lang/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

This guide shows how to run `.homo` programs locally, measure basic performance, and understand current runtime capabilities.

## Why Homo? (Python vs Homo Comparison)

Homo is designed specifically to exceed expectations by completely stripping away complex syntax like semicolons, brackets, and cryptic slicing operators. It is built to be read exactly like plain English, making it the absolute easiest language for children and beginners to learn logic.

Look at how much simpler a standard algorithm (checking if a word is a palindrome) is in Homo compared to Python:

**The Python Way (Hard to read for beginners):**
```python
def check_palindrome(word):
    # Beginners struggle with cryptic syntax like [::-1]
    reversed_word = word[::-1]
    if word == reversed_word:
        return True
    else:
        return False

my_word = "racecar"
result = check_palindrome(my_word)
print("Is palindrome:", result)
```

**The Homo Way (Reads like English):**
```homo
define check_palindrome word
    calculate reversed as reverse(word)
    
    if word == reversed
        return true
    otherwise
        return false

set my_word as "racecar"
call check_palindrome my_word

show "Is palindrome:"
show result
```

**Another Example: The Machine Learning Nightmare vs Homo**
Training an AI is usually terrifying for beginners. Look at the difference:

**The Python Way (Scary for Beginners):**
```python
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

df = pd.read_csv("data.csv")
X = df.drop(columns=["weight"])
y = df["weight"]

model = RandomForestRegressor()
model.fit(X, y)

predictions = model.predict(X)
rmse = mean_squared_error(y, predictions, squared=False)
print("Score:", rmse)
```

**The Homo Way (Just 3 lines of plain English!):**
```homo
load data "data.csv" as df

# Create and train the AI in one sentence!
learn from df to guess "weight" as my_ai
test my_ai on df as score metric "rmse"

show score
```

Homo achieves native Python-level power without any of the frustrating technical hurdles!

## 1. Prerequisites

- Python 3.8+ installed
- Files in the same folder:
  - `main.py`
  - `lexer.py`
  - `parser.py`
  - `ast_nodes.py`
  - `interpreter.py`

### Optional Packages (Advanced Features)

To use the advanced Data Science, Machine Learning, and Media features, install the following optional packages. (Website/App building features have been explicitly removed to streamline the architecture).

**Lightweight / Data Science:**
```bash
pip install pandas numpy scikit-learn matplotlib psutil requests Pillow reportlab cryptography websocket-client pyttsx3 joblib
```

**Medium / Audio & ML:**
```bash
pip install xgboost librosa sounddevice soundfile
```

## 2. Run a Homo program

Basic usage:

```bash
python3 main.py your_file.homo
```

Enable debug output (prints source, tokens, AST):

```bash
python3 main.py your_file.homo --debug
```

## 3. Minimal example

Create a file `hello.homo`:

```homo
show "Hello, Homo!"
set name as "Karthik"
show "Welcome, {name}!"

calculate sum as 10 plus 25
show sum
```

Run it:

```bash
python3 main.py hello.homo
```

## 4. Control flow & Functions example

```homo
set age as 21

if age is greater than 18
    show "Adult"
otherwise
    show "Minor"

define greet name
    show "Hello, {name}!"

call greet "World"
```

## 5. Data Science & Machine Learning

Homo now natively supports calling pandas, numpy, and scikit-learn functions natively if the packages are installed. 

**Example Data Science flow:**
```homo
load data "data.csv" as df
show data df 5 rows
describe data df

show chart line of df
```

**Example ML flow (Kid-Friendly):**
```homo
# 1. Create your AI
make AI "random_forest" as my_ai

# 2. Teach it using your data
teach my_ai using df to guess "target_column"

# 3. Test how smart it is!
test my_ai on df as results
show results
```

**Super Simple ML flow:**
```homo
learn from df to guess "target_column" as smart_bot
test smart_bot on df as score
show score
```

## 6. Measuring efficiency (basic)

You can time execution using the shell:

```bash
/usr/bin/time -p python3 main.py your_file.homo
```

This prints:
- **real**: total wall time
- **user**: CPU time in user mode
- **sys**: CPU time in kernel mode

## 7. Known runtime limitations

Some advanced AST nodes exist in `ast_nodes.py` and are parsed, but are not implemented in the runtime (interpreter). When used, they print a message like:

```
[homo] <feature> not supported in this runtime (<NodeName>)
```

Currently **unsupported** categories (unless "Heavy" dependencies are installed and implemented):
- Deep learning (PyTorch)
- Local LLM helpers
- Computer vision helpers
- Generative helpers
- NLP helpers

Core language features (variables, control flow, functions, file ops, logging, etc.) and Data Science / ML are fully implemented.

## 8. Common issues

- **File not found**: Ensure the `.homo` path is correct.
- **Import/use issues**: When using `use module`, keep `.homo` modules relative to the running file or current working directory.
- **Missing optional packages**: Install the packages listed in section 1 if a feature needs them.
- **Removed Features**: Web scaffolding, Desktop App (Tkinter), and GUI features have been removed from this distribution.

## 9. Where output goes

- Standard output (terminal) is used for `show` and most runtime logs.
- `log` writes to `app.log` in the current working directory.
- `export pdf` will create a basic PDF in the working directory.
