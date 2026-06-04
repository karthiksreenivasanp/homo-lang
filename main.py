#!/usr/bin/env python3
import sys
import os

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

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

def main():
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"Homo Language v{HOMO_VERSION}")
        return

    debug = "--debug" in sys.argv
    args = [a for a in sys.argv[1:] if a not in ("--debug", "--version", "-v")]

    if len(args) == 0:
        repl()
        return

    file_path = args[0]

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
        interpreter.execute(ast)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
