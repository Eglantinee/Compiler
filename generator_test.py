from compiler import Lexer, Parser, Compile
import os
import sys

null = open(os.devnull, "w")
sys.stdout = null
a = Lexer('lab1.c')
a = a.next_token()
p = Parser(a)
ast = p.parse()

com = Compile()
com.compile(ast)
com.printer()

null.close()
