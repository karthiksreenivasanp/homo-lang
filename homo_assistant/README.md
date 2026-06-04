# 🤖 Homo Language AI Assistant

This is an Agentic AI Assistant specialized entirely in the **Homo programming language**. 
You can chat with this AI to ask questions about Homo syntax, generate code, or have it autonomously **create, read, and edit Homo scripts** directly on your computer!

## Features
- ⚡ **Lightning Fast & Free**: Uses the Groq API to run large open-source models like Llama-3 at incredible speeds completely for free.
- 📂 **Autonomous Agent Tools**: The AI can execute tools to create new `.homo` scripts, read existing files, and apply edits to your workspace.
- 🧠 **Native Homo Knowledge**: Pre-loaded with a comprehensive Homo Cheat Sheet, so it knows exactly how to write valid code (no semicolons, correct indentation, ML syntax, etc).

---

## 🛠️ Setup Guidelines

### 1. Requirements
Ensure you have Python 3 installed on your machine.
It is highly recommended to use a virtual environment.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate it (Linux/Mac)
source venv/bin/activate
# Or on Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies
Install all required libraries (Streamlit, LangChain, etc.) using `pip`:

```bash
pip install -r requirements.txt
```

### 3. Launch the Application
Run the Streamlit web application:

```bash
streamlit run app.py
```
This will automatically open your web browser to `http://localhost:8501`.

---

## 🔑 Getting your Free API Key

By default, the Assistant requires a Groq API key to process your requests with great performance. **This is completely free.**

1. Go to the [Groq Console](https://console.groq.com/).
2. Create a free account or sign in.
3. Navigate to **API Keys** and generate a new key.
4. Launch the AI Assistant (`streamlit run app.py`).
5. Look at the left sidebar in the web app, select **"Groq (Fast Cloud)"**, and paste your API key there.

> **Security Note:** Your API Key is **never** saved to your disk or stored in this repository. It only lives in your local browser session while the app is running, ensuring maximum security.

## Offline Mode (Ollama)
If you prefer to run the LLM entirely on your local machine without using the cloud, you can use Ollama:
1. Download and install [Ollama](https://ollama.com/).
2. Run a model in your terminal, for example: `ollama run llama3`.
3. Open the Homo AI Assistant, select **"Ollama (Local)"** from the sidebar, type `llama3` as the model name, and start chatting!
