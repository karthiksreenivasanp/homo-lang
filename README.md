<div align="center">
  <h1>🌟 Homo Programming Language</h1>
  <p><b>A powerful, intuitive, and kid-friendly programming language with built-in Auto-Healing Machine Learning!</b></p>
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green" alt="Python">
  <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build">
</div>

---

Welcome to **Homo**! Homo is a brand new, natural-language programming environment designed specifically to introduce children, beginners, and students to complex concepts like Logic, Algorithms, and **Machine Learning** without the intimidating syntax of traditional languages.

No brackets. No semicolons. Just pure, readable English!

## ✨ Key Features
- 🧠 **Plain English Machine Learning:** Train Random Forests, SVMs, and Logistic Regressions using simple sentences like `teach my_ai using df`.
- 🤖 **Auto-Healing Compiler (100% Offline):** Made a typo? Wrote invalid syntax? The Homo compiler will magically pause, send your broken code to a local AI, permanently fix your file on disk, and automatically restart!
- 📊 **Auto-Detecting Metrics:** You don't need to know whether to use RMSE or Accuracy. Homo automatically detects if your data is categorical or continuous and picks the right metric for you!
- 🗣️ **Conversational AI Assistant:** Includes an interactive web app where kids can talk to an AI mentor to learn Homo code instantly!

---

## 🚀 Quick Setup & Installation

Setting up Homo is incredibly easy. It runs entirely on Python!

### 1. Prerequisites
Make sure you have Python 3.8+ installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/karthiksreenivasanp/homo-lang.git
cd homo-lang
```

### 3. Install Dependencies
Homo requires some standard data science libraries to power its incredible built-in Machine Learning engine:
```bash
pip install pandas scikit-learn requests
```

---

## 💻 How to Run Your First Code

Homo files end in `.homo`. To run any script, simply pass it to the compiler (`main.py`):

```bash
# Run a specific file
python3 main.py examples/basics/test_loop.homo

# Or enter Interactive Mode (REPL)
python3 main.py
```

---

## 📖 The Homo Syntax Cheat Sheet

Here are some quick examples of how elegant Homo code is!

### Basics
```homo
set score as 100
show "Your score is: " + score

ask "What is your name?" name
show "Hello " + name
```

### Loops & Logic
```homo
if score > 50
    show "You passed!"
otherwise
    show "Try again!"

repeat 3 times
    show "Hooray!"
```

### Machine Learning (The Magic!)
Train and cross-validate an entire AI model in just 4 lines of code:
```homo
# Load data and create a Random Forest
load data "data.csv" as df
make AI "smart_guesser" as bot

# Train the AI
teach bot using df to guess "weight"

# Cross-validate the model 3 times
check bot 3 times on df to guess "weight" as cv_scores
show cv_scores
```

---

## 🤖 Offline Auto-Healing Compiler

Homo features an unprecedented **Auto-Healing Engine**. If a child makes a syntax error or a logical mistake, the compiler will *not* crash! Instead, it will automatically connect to a local AI to fix the script on the hard drive and run it again.

**To enable 100% Offline Auto-Healing (No Internet Required):**
1. Install [Ollama](https://ollama.com).
2. Open your terminal and start the AI engine: `ollama run llama3`
3. That's it! Homo will automatically detect the local server and use it to magically fix broken code in the background!

*(If you don't have Ollama, you can also use Groq's cloud API by setting the `GROQ_API_KEY` environment variable).*

---

## 📁 Repository Structure

We've neatly organized the repository so it's easy to explore:

- **`/` (Root):** Contains the core compiler files (`main.py`, `lexer.py`, `parser.py`, `interpreter.py`).
- **`/examples/`:** Contains incredible examples of what Homo can do!
  - `/machine_learning/`: Advanced ML pipelines (KNN, Linear, SVM).
  - `/sorting/`: Famous algorithms written in Homo (Bubble sort, Merge sort).
  - `/data/`: Sample CSV files for ML training.
- **`/tests/`:** Contains unit tests and the Master Test Suite (`find_bugs.homo`) to ensure the language is 100% stable.
- **`/homo_assistant/`:** The Streamlit web app that runs the conversational AI mentor!

---

## 🤝 Contributing
Want to help make Homo even better? We welcome contributions! Feel free to open an issue, submit a Pull Request, or add more algorithms to the `examples/` folder.

<div align="center">
  <b>Built with ❤️ to make programming and AI accessible to everyone!</b>
</div>
