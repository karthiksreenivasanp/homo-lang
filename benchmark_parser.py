import time

from lexer import Lexer
from parser import Parser

source = "\n".join(
    ['show "hello world"' for _ in range(100000)]
)

lexer = Lexer()
parser = Parser()

tokens = lexer.tokenize(source)

start = time.perf_counter()

ast = parser.parse(tokens)

end = time.perf_counter()

print("AST Nodes:", len(ast))
print("Time:", end-start)
print("Nodes/sec:", len(ast)/(end-start))