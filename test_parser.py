from compiler import Lexer, Parser
from collections.abc import Iterable

nodes = ['VAR', 'CONST', 'RET', 'EXPR', 'FUNC', 'UNOP', 'BINOP', 'BIN_PROD', 'BIN_DIV', 'BIN_XOR', 'FACTOR', 'TERM',
         'DECL', 'STMT', 'ID', 'TERNARY', 'BLOCK', 'PROG']

file = 'lab1.c'
lex = Lexer(file)
lexems = lex.next_token()
pars = Parser(lexems)
ast = pars.parse()

print("#" * 30)
for i in lexems:
    print(i)


def tree_ast(ast, n):
    if ast is None:
        return
    print(' ' * 2 * n, nodes[ast.kind], end=" ")
    if ast.value:
        print(ast.value)
    else:
        print(" ")
    if ast.op2:
        print(' ' * 2 * (n + 1), "op2:")
        # if ast.op2.value:
        #     print(ast.op2.value)
        # else:
        #     print("")
        # if ast.op2.op1 is not None:
        tree_ast(ast.op2, n + 3)
    if ast.op3:
        print(' ' * 2 * (n + 1), "op3:")
        # if ast.op3.value:
        #     print(ast.op3.value)
        # else:
        #     print("")
        # if ast.op3.op1 is not None:
        tree_ast(ast.op3, n + 3)
    if isinstance(ast.op1, Iterable):
        for i in ast.op1:
            tree_ast(i, n + 1)
    else:
        tree_ast(ast.op1, n + 1)


tree_ast(ast, 1)
