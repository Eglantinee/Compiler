from compiler import Lexer, Parser
from collections.abc import Iterable

nodes = ['VAR', 'CONST', 'RET', 'EXPR', 'FUNC', 'UNOP', 'BINOP', 'BIN_PROD', 'BIN_DIV', 'BIN_XOR', 'FACTOR', 'TERM', 'DECL', 'STMT', 'ID', 'PROG']

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
    # if ast.kind == Parser.CONST:
    #     print(ast.value)
    # elif ast.kind == Parser.ID:
    #     print(ast.value)
    else:
        print(" ")
    if isinstance(ast.op1, Iterable):
        for i in ast.op1:
            tree_ast(i, n + 1)
    else:
        tree_ast(ast.op1, n + 1)


tree_ast(ast, 1)
