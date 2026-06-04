import time

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

with open("perf.homo") as f:
    source = f.read()

lexer = Lexer()
parser = Parser()
interpreter = Interpreter()

tokens = lexer.tokenize(source)
ast = parser.parse(tokens)

start = time.perf_counter()

interpreter.execute(ast)

end = time.perf_counter()

print("Execution:", end-start)