#!/usr/bin/env python3
import sys
import os

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
import requests
import json

HOMO_VERSION = "1.0.0"

def repl():
    print(f"Homo Language Interactive Mode v{HOMO_VERSION}")
    print("Type 'exit' or 'quit' to leave.")
    lexer = Lexer()
    parser = Parser()
    interpreter = Interpreter(base_dir=os.getcwd())

    while True:
        try:
            line = input("homo> ")
            if line.strip() in ("exit", "quit"):
                break
            if not line.strip():
                continue
            
            tokens = lexer.tokenize(line)
            ast = parser.parse(tokens)
            interpreter.execute(ast)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
        except Exception as e:
            print(f"Error: {e}")

def auto_heal(file_path, source, error_msg):
    print(f"\n[homo] 🤖 Auto-Healing triggered for '{file_path}'...")
    
    cheat_sheet = ""
    try:
        cs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "homo_assistant", "homo_cheat_sheet.txt")
        if os.path.exists(cs_path):
            with open(cs_path, "r", encoding="utf-8") as f:
                cheat_sheet = f.read()
    except:
        pass
        
    prompt = f"""You are an expert compiler for the Homo programming language.
The user wrote a Homo script that crashed with the following error:
{error_msg}

Here are the rules of the Homo language:
{cheat_sheet}

Here is the broken script:
```homo
{source}
```

Fix the script so it works perfectly. Reply ONLY with the fixed Homo code. Do not include any markdown formatting, explanations, or backticks. Just the raw code."""
    try:
        fixed_code = None
        # Try offline Ollama first
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3", "prompt": prompt, "stream": False},
                timeout=30
            )
            response.raise_for_status()
            fixed_code = response.json().get("response", "").strip()
        except requests.exceptions.RequestException:
            # Fallback to Groq
            groq_key = os.environ.get("GROQ_API_KEY")
            if groq_key:
                print("[homo] Ollama offline. Falling back to Groq cloud API...")
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                data = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
                response.raise_for_status()
                fixed_code = response.json()["choices"][0]["message"]["content"].strip()
            else:
                print("[homo] Error: Offline Ollama server is not running and GROQ_API_KEY is not set.")
                print("To use offline auto-healing, install Ollama and run 'ollama run llama3'.")
                return False

        if fixed_code.startswith("```"):
            lines = fixed_code.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            fixed_code = "\n".join(lines).strip()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        
        print("[homo] ✨ Script automatically fixed and updated!")
        return True
    except Exception as e:
        print(f"[homo] Auto-heal failed: {e}")
        return False

def run_file(file_path, debug=False, is_retry=False):
    import io
    import sys
    source = ""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            source = file.read()

        if debug:
            print("\n=== SOURCE CODE ===")
            print(source)

        lexer = Lexer()
        tokens = lexer.tokenize(source)

        if debug:
            print("\n=== TOKENS ===")
            print(tokens)

        parser = Parser()
        ast = parser.parse(tokens)

        if debug:
            print("\n=== AST ===")
            print(ast)
            print("\n=== PROGRAM OUTPUT ===")

        interpreter = Interpreter(base_dir=os.path.dirname(os.path.abspath(file_path)))
        
        # Capture stdout to detect soft errors
        old_stdout = sys.stdout
        sys.stdout = capture_out = io.StringIO()
        
        try:
            interpreter.execute(ast)
        finally:
            sys.stdout = old_stdout
            
        output_text = capture_out.getvalue()
        if output_text.strip():
            print(output_text, end="")
            
        # Detect soft errors that Homo prints instead of raising
        lower_out = output_text.lower()
        if "[homo] error:" in lower_out or "variable" in lower_out and "not found" in lower_out or "unknown model" in lower_out or "error:" in lower_out or "traceback" in lower_out:
            raise Exception(f"Homo Execution Error detected in output:\n{output_text}")
            
        return True

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return False
    except Exception as e:
        if not is_retry and source:
            print(f"Error: {e}")
            if auto_heal(file_path, source, str(e)):
                print("Restarting execution...\n" + "-"*40)
                return run_file(file_path, debug=debug, is_retry=True)
        else:
            print(f"Error persists: {e}")
        return False

def main():
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"Homo Language v{HOMO_VERSION}")
        return

    debug = "--debug" in sys.argv
    args = [a for a in sys.argv[1:] if a not in ("--debug", "--version", "-v")]

    if len(args) == 0:
        repl()
        return

    run_file(args[0], debug=debug)

if __name__ == "__main__":
    main()
