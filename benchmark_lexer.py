import time
from lexer import Lexer

source = "\n".join(
    ['show "hello world"' for _ in range(100000)]
)

lexer = Lexer()

start = time.perf_counter()

tokens = lexer.tokenize(source)

end = time.perf_counter()

print("Tokens:", len(tokens))
print("Time:", end - start, "seconds")
print("Throughput:", len(tokens)/(end-start), "tokens/sec")